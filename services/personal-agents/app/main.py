"""
Personal Agents Service v2 — Hermes-Stil Agenten für Sven, Samira & Sineo

Zone: FAMILY_PRIVATE
Kanonischer Datenspeicher: /Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner/

ANTI-HALLUZINATION v2:
  - Hermes-Stil System-Prompt: Regeln ZUERST, Fakten danach
  - Nur Fakten aus profil.yaml werden verwendet
  - Neue Fakten → sofort in profil.yaml + memory/knowledge_graph.json
  - Kein Fakt aus KI-Training über Familienmitglieder
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------------
# Konfiguration — Datenspeicher als primäre Quelle
# ---------------------------------------------------------------------------

# Primär: Datenspeicher-Pfad (canonical source of truth)
BENUTZER_BASE = Path(os.getenv(
    "BENUTZER_BASE",
    "/Datenspeicher/OpenDisruption_Datenstruktur/Benutzer-Ordner"
))
# Fallback: lokales /app/profiles (für Docker-Volume-Kompatibilität)
PROFILES_FALLBACK = Path(os.getenv("PROFILES_DIR", "/app/profiles"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
GH_TOKEN = os.getenv("GH_TOKEN", "")
GITHUB_MODELS_URL = "https://models.github.ai/inference/v1"

ALLOWED_SUBJECTS = {"sven", "samira", "sineo"}
# Mapping subject → Ordnername in Benutzer-Ordner
SUBJECT_DIR = {"sven": "Sven", "samira": "Samira", "sineo": "Sineo"}

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Personal Agents — Sven, Samira & Sineo",
    description=(
        "Hermes-Stil persönliche Agenten. "
        "Fakten aus /Datenspeicher/.../Benutzer-Ordner. Keine Halluzinationen."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Profile I/O — Datenspeicher first, Fallback /app/profiles
# ---------------------------------------------------------------------------

def _profile_path(subject: str) -> Path:
    """Gibt den kanonischen Pfad zur profil.yaml zurück."""
    folder = SUBJECT_DIR.get(subject, subject.capitalize())
    datenspeicher_path = BENUTZER_BASE / folder / "agent" / "profil.yaml"
    if datenspeicher_path.exists():
        return datenspeicher_path
    # Fallback: lokales /app/profiles/{subject}.yaml
    return PROFILES_FALLBACK / f"{subject}.yaml"


def _memory_path(subject: str) -> Path:
    """Gibt den Pfad zur knowledge_graph.json zurück."""
    folder = SUBJECT_DIR.get(subject, subject.capitalize())
    return BENUTZER_BASE / folder / "agent" / "memory" / "knowledge_graph.json"


def load_profile(subject: str) -> Dict[str, Any]:
    path = _profile_path(subject)
    if not path.exists():
        raise HTTPException(404, f"Profil '{subject}' nicht gefunden unter {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_profile(subject: str, profile: Dict[str, Any]) -> None:
    path = _profile_path(subject)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            profile, f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        )
    logger.info(f"[{subject}] Profil gespeichert → {path}")


def sync_fact_to_memory(subject: str, fact: Dict[str, Any]) -> None:
    """Schreibt einen neuen Fakt in die knowledge_graph.json (Hermes MCP Memory)."""
    mem_path = _memory_path(subject)
    try:
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        graph: Dict = {"entities": [], "relations": []}
        if mem_path.exists():
            with open(mem_path, "r", encoding="utf-8") as f:
                graph = json.load(f)
        entities = graph.setdefault("entities", [])
        entity = next((e for e in entities if e.get("name") == subject), None)
        if entity is None:
            entity = {"name": subject, "entityType": "person", "observations": []}
            entities.append(entity)
        observation = (
            f"[{fact.get('category', 'allgemein')}] {fact['fact']} "
            f"(Stand: {fact.get('learned_at', datetime.now().strftime('%Y-%m-%d'))})"
        )
        obs_list = entity.setdefault("observations", [])
        if observation not in obs_list:
            obs_list.append(observation)
        with open(mem_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        logger.info(f"[{subject}] Memory-Sync → {mem_path.name}: {observation[:60]}")
    except Exception as e:
        logger.error(f"[{subject}] Memory-Sync fehlgeschlagen: {e}")


# ---------------------------------------------------------------------------
# Hermes-Stil System-Prompt-Builder
# ---------------------------------------------------------------------------
# WICHTIG: Reihenfolge ist kritisch für Anti-Halluzination.
# 1. Identität (wer bin ich)
# 2. Anti-Halluzinations-Regeln → ZUERST damit das Modell sie priorisiert
# 3. Bekannte Fakten (nur verifizierte)
# 4. Nächste offene Frage
# 5. Fähigkeiten + Stil

def build_system_prompt(profile: Dict[str, Any]) -> str:
    """Baut den Hermes-Stil System-Prompt aus dem Profil."""
    persona = profile.get("persona", {})
    display_name = profile.get("display_name", "die Person")
    lang = persona.get("language", {})

    # 1. Identität
    identity = persona.get("identity", f"Ich bin der persönliche KI-Assistent für {display_name}.")

    # 2. Anti-Halluzination (aus Profil — ZUERST im Prompt!)
    anti_h = persona.get("anti_hallucination", f"""
══════════════════════════════════════════════════════════════
⚠️  EISERNE REGEL — ABSOLUT VERBOTEN DIES ZU BRECHEN
══════════════════════════════════════════════════════════════
Ich spreche NUR über Fakten die unter "BEKANNTE FAKTEN" gelistet sind.
WENN EIN FAKT FEHLT → "Das weiß ich noch nicht, {display_name}." + eine Folgefrage.
NIEMALS: Alter, Beruf, Hobbys, Eigenschaften ERFINDEN.
══════════════════════════════════════════════════════════════""")

    # 3. Fakten-Block
    facts: List[Dict] = profile.get("facts", [])
    if facts:
        facts_lines = "\n".join(
            f"  {'✅' if f.get('confidence') == 'verified' else '⚠️'} "
            f"[{f.get('category', '?')}] {f['fact']}"
            for f in facts
        )
        facts_block = f"\n## ✅ BEKANNTE FAKTEN über {display_name}:\n{facts_lines}\n"
    else:
        facts_block = (
            f"\n## ⚠️ BEKANNTE FAKTEN über {display_name}:\n"
            f"  NOCH KEINE FAKTEN GESPEICHERT — ich muss {display_name} erst kennenlernen!\n"
        )

    # 4. Nächste offene Frage
    unknowns = profile.get("unknown_facts", [])
    high = [q for q in unknowns if q.get("priority") == "high"]
    next_q = (high or unknowns or [{}])[0].get("question")
    next_block = ""
    if next_q:
        next_block = f"\n## 📌 NÄCHSTE PRIORITÄT:\nFalls natürliche Gelegenheit: frage nach → {next_q}\n"

    # 5. Stil
    style = lang.get("style", "warm, direkt")
    tone = lang.get("tone", "persönlich")
    caps = persona.get("capabilities", [])
    caps_block = ""
    if caps:
        caps_block = "\n## 💡 WOMIT ICH HELFE:\n" + "\n".join(f"  - {c}" for c in caps) + "\n"

    return (
        f"{identity}\n\n"
        f"{anti_h}\n"
        f"{facts_block}"
        f"{next_block}"
        f"{caps_block}"
        f"\n## SPRACHE & STIL:\n"
        f"  - Immer Deutsch (außer {display_name} schreibt Englisch)\n"
        f"  - Stil: {style}\n"
        f"  - Ton: {tone}\n"
        f"  - Duzen\n"
        f"\n## WENN NEUE FAKTEN GETEILT WERDEN:\n"
        f"  - Kurz bestätigen und sagen: 'Gespeichert ✓'\n"
        f"  - Sofort im Gespräch verwenden\n"
    )


# ---------------------------------------------------------------------------
# LLM-Aufruf (Ollama → GitHub Fallback)
# ---------------------------------------------------------------------------

async def call_llm(messages: List[Dict], profile: Dict[str, Any]) -> str:
    """Ruft das im Profil konfigurierte Modell auf."""
    model = profile.get("persona", {}).get("model", {}).get("primary", "qwen2.5:14b")
    fallback = profile.get("persona", {}).get("model", {}).get("fallback", "openai/gpt-4.1-mini")

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Primär: Ollama (lokal)
        try:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "")
            logger.warning(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Ollama nicht erreichbar: {e}")

        # Fallback: GitHub Models (nur wenn GH_TOKEN gesetzt)
        if GH_TOKEN:
            try:
                resp = await client.post(
                    f"{GITHUB_MODELS_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {GH_TOKEN}"},
                    json={"model": fallback, "messages": messages},
                    timeout=60.0,
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                logger.error(f"GitHub Models HTTP {resp.status_code}")
            except Exception as e:
                logger.error(f"GitHub Models Fallback fehlgeschlagen: {e}")

    return (
        "Ich kann gerade keine Verbindung zum KI-Modell aufbauen. "
        "Bitte versuche es in einem Moment erneut."
    )


# ---------------------------------------------------------------------------
# Pydantic-Modelle
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = None


class ChatResponse(BaseModel):
    reply: str
    new_facts_learned: List[str] = []
    next_unknown_question: Optional[str] = None


class FactCreate(BaseModel):
    category: str
    fact: str
    confidence: str = "verified"
    source: str = "user-confirmed"


class FactResponse(BaseModel):
    id: str
    category: str
    fact: str
    confidence: str
    learned_at: str


class ProfileResponse(BaseModel):
    subject: str
    display_name: str
    relation: str
    fact_count: int
    unknown_count: int
    facts: List[FactResponse]
    next_questions: List[str]
    persona_name: str
    model: str
    profile_path: str


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _extract_learned_facts(message: str, subject: str) -> List[Dict[str, Any]]:
    """Erkennt Fakten-Aussagen im Nutzer-Input via Keyword-Matching."""
    learned: List[Dict[str, Any]] = []
    msg_lower = message.lower().strip()
    keywords = [
        "ich bin ", "ich habe ", "ich mag ", "ich liebe ", "ich hasse ",
        "mein name ist", "ich heiße", "ich gehe in die", "ich gehe in klasse",
        "ich spiele ", "ich programmiere", "ich lerne ", "ich wohne ",
        "ich arbeite ", "ich studiere", "meine klasse", "mein hobby",
        "jahre alt", "klasse ", "mein liebling",
    ]
    if any(kw in msg_lower for kw in keywords):
        learned.append({
            "id": f"auto-{uuid.uuid4().hex[:6]}",
            "category": "auto-learned",
            "fact": message[:300].strip(),
            "confidence": "inferred",
            "source": "conversation",
            "learned_at": datetime.now().strftime("%Y-%m-%d"),
        })
    return learned


def _get_next_unknown_question(profile: Dict) -> Optional[str]:
    unknowns = profile.get("unknown_facts", [])
    high = [q for q in unknowns if q.get("priority") == "high"]
    queue = high or unknowns
    return queue[0].get("question") if queue else None


def _validate_subject(subject: str) -> None:
    if subject not in ALLOWED_SUBJECTS:
        raise HTTPException(404, f"Unbekanntes Profil '{subject}'. Erlaubt: {sorted(ALLOWED_SUBJECTS)}")


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    profiles_status = []
    for subject in sorted(ALLOWED_SUBJECTS):
        path = _profile_path(subject)
        if path.exists():
            try:
                p = load_profile(subject)
                persona = p.get("persona", {})
                profiles_status.append({
                    "subject": subject,
                    "display_name": p.get("display_name", subject.capitalize()),
                    "fact_count": len(p.get("facts", [])),
                    "unknown_count": len(p.get("unknown_facts", [])),
                    "model": persona.get("model", {}).get("primary", "qwen2.5:14b"),
                    "profile_path": str(path),
                })
            except Exception as e:
                profiles_status.append({"subject": subject, "error": str(e)})
        else:
            profiles_status.append({"subject": subject, "status": "profil nicht gefunden"})
    return {
        "status": "ok",
        "service": "personal-agents",
        "version": "2.0.0",
        "benutzer_base": str(BENUTZER_BASE),
        "profiles": profiles_status,
    }


@app.get("/{subject}/profile", response_model=ProfileResponse)
async def get_profile(subject: str):
    _validate_subject(subject)
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    unknowns = profile.get("unknown_facts", [])
    persona = profile.get("persona", {})
    high_q = [q["question"] for q in unknowns if q.get("priority") == "high"]
    med_q = [q["question"] for q in unknowns if q.get("priority") == "medium"]
    return ProfileResponse(
        subject=subject,
        display_name=profile.get("display_name", subject.capitalize()),
        relation=profile.get("relation", profile.get("relation_to_sven", "Familienmitglied")),
        fact_count=len(facts),
        unknown_count=len(unknowns),
        facts=[
            FactResponse(
                id=f.get("id", f"f{i}"),
                category=f.get("category", "?"),
                fact=f["fact"],
                confidence=f.get("confidence", "verified"),
                learned_at=f.get("learned_at", "unbekannt"),
            )
            for i, f in enumerate(facts)
        ],
        next_questions=(high_q + med_q)[:5],
        persona_name=persona.get("name", "Kirobi"),
        model=persona.get("model", {}).get("primary", "qwen2.5:14b"),
        profile_path=str(_profile_path(subject)),
    )


@app.post("/{subject}/facts", response_model=FactResponse)
async def add_fact(subject: str, fact_data: FactCreate):
    _validate_subject(subject)
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    new_id = f"f{len(facts) + 1:03d}"
    new_fact: Dict[str, Any] = {
        "id": new_id,
        "category": fact_data.category,
        "fact": fact_data.fact,
        "confidence": fact_data.confidence,
        "source": fact_data.source,
        "learned_at": datetime.now().strftime("%Y-%m-%d"),
    }
    facts.append(new_fact)
    profile["facts"] = facts
    save_profile(subject, profile)
    sync_fact_to_memory(subject, new_fact)
    logger.info(f"[{subject}] ✅ Neuer Fakt: {fact_data.fact[:80]}")
    return FactResponse(
        id=new_id,
        category=new_fact["category"],
        fact=new_fact["fact"],
        confidence=new_fact["confidence"],
        learned_at=new_fact["learned_at"],
    )


@app.delete("/{subject}/facts/{fact_id}")
async def delete_fact(subject: str, fact_id: str):
    _validate_subject(subject)
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    original = len(facts)
    profile["facts"] = [f for f in facts if f.get("id") != fact_id]
    if len(profile["facts"]) == original:
        raise HTTPException(404, f"Fakt '{fact_id}' nicht gefunden")
    save_profile(subject, profile)
    return {"deleted": fact_id}


@app.delete("/{subject}/unknown/{question_id}")
async def resolve_unknown(subject: str, question_id: str):
    _validate_subject(subject)
    profile = load_profile(subject)
    unknowns = profile.get("unknown_facts", [])
    profile["unknown_facts"] = [q for q in unknowns if q.get("id") != question_id]
    save_profile(subject, profile)
    return {"resolved": question_id}


@app.get("/{subject}/interview")
async def get_interview_questions(subject: str, limit: int = 5):
    _validate_subject(subject)
    profile = load_profile(subject)
    unknowns = profile.get("unknown_facts", [])
    high = [q for q in unknowns if q.get("priority") == "high"]
    medium = [q for q in unknowns if q.get("priority") == "medium"]
    low = [q for q in unknowns if q.get("priority") == "low"]
    queue = (high + medium + low)[:limit]
    facts = profile.get("facts", [])
    total = max(len(facts) + len(unknowns), 1)
    return {
        "subject": subject,
        "display_name": profile.get("display_name"),
        "total_unknown": len(unknowns),
        "next_questions": [q["question"] for q in queue],
        "fact_count": len(facts),
        "profile_complete_pct": round(len(facts) / total * 100, 1),
        "profile_path": str(_profile_path(subject)),
    }


@app.get("/{subject}/intro")
async def introduce_agent(subject: str):
    _validate_subject(subject)
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    name = profile.get("display_name", subject.capitalize())
    unknowns = profile.get("unknown_facts", [])
    high_q = [q["question"] for q in unknowns if q.get("priority") == "high"]
    persona = profile.get("persona", {})
    total = max(len(facts) + len(unknowns), 1)

    if not facts:
        intro = (
            f"Hey {name}! Ich bin Kirobi — dein persönlicher KI-Begleiter. "
            f"Ich lerne dich gerade erst kennen — ich weiß noch nichts über dich. "
            f"Damit ich dir wirklich helfen kann: "
            + (high_q[0] if high_q else "Magst du mir etwas über dich erzählen?")
        )
    else:
        intro = (
            f"Hey {name}! Ich bin Kirobi. Ich kenne dich schon ein bisschen "
            f"({len(facts)} gespeicherte Fakten). Ich helfe dir bei allem was du brauchst."
        )
        if high_q:
            intro += f" Ich würde noch gerne wissen: {high_q[0]}"

    return {
        "subject": subject,
        "display_name": name,
        "persona_name": persona.get("name", "Kirobi"),
        "model": persona.get("model", {}).get("primary", "qwen2.5:14b"),
        "intro": intro,
        "known_facts": len(facts),
        "unknown_facts": len(unknowns),
        "next_question": high_q[0] if high_q else None,
        "profile_complete_pct": round(len(facts) / total * 100, 1),
        "profile_path": str(_profile_path(subject)),
    }


@app.post("/{subject}/chat", response_model=ChatResponse)
async def chat_with_agent(subject: str, request: ChatRequest):
    """
    Hermes-Stil Chat — GARANTIE: Nur gespeicherte Fakten.
    Neue Fakten → sofort in profil.yaml + memory/knowledge_graph.json.
    """
    _validate_subject(subject)
    profile = load_profile(subject)
    system_prompt = build_system_prompt(profile)

    messages: List[Dict] = [{"role": "system", "content": system_prompt}]
    if request.conversation_history:
        messages.extend(request.conversation_history[-12:])
    messages.append({"role": "user", "content": request.message})

    reply = await call_llm(messages, profile)

    # Auto-Fakten aus Nutzer-Nachricht extrahieren und speichern
    new_raw = _extract_learned_facts(request.message, subject)
    saved_facts: List[str] = []
    for raw_fact in new_raw:
        profile.setdefault("facts", []).append(raw_fact)
        saved_facts.append(raw_fact["fact"])
        sync_fact_to_memory(subject, raw_fact)
    if saved_facts:
        save_profile(subject, profile)

    next_q = _get_next_unknown_question(profile)
    return ChatResponse(
        reply=reply,
        new_facts_learned=saved_facts,
        next_unknown_question=next_q,
    )


@app.post("/{subject}/learn")
async def teach_fact(subject: str, fact_data: FactCreate):
    """Alias für POST /{subject}/facts — explizites Lernen eines Fakts."""
    return await add_fact(subject, fact_data)
