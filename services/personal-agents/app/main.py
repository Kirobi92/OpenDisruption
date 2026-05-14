"""
Personal Agents Service — Fakten-basierte Agenten für Samira & Sineo

Zone: FAMILY_PRIVATE
ANTI-HALLUZINATION: Alle Antworten basieren AUSSCHLIESSLICH auf gespeicherten Fakten.
Unbekannte Fakten → gezielte Nachfrage statt Erfindung.
"""

from __future__ import annotations

import asyncio
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

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
PROFILES_DIR = Path(os.getenv("PROFILES_DIR", "/app/profiles"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
GH_TOKEN = os.getenv("GH_TOKEN", "")
GITHUB_MODELS_URL = "https://models.github.ai/inference/v1"
FALLBACK_MODEL = "openai/gpt-4.1-mini"

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Personal Agents — Samira & Sineo",
    description="Fakten-basierte persönliche Agenten. Keine Halluzinationen.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Profile I/O
# ---------------------------------------------------------------------------

def _profile_path(subject: str) -> Path:
    return PROFILES_DIR / f"{subject}.yaml"


def load_profile(subject: str) -> Dict[str, Any]:
    path = _profile_path(subject)
    if not path.exists():
        raise HTTPException(404, f"Profil '{subject}' nicht gefunden")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_profile(subject: str, profile: Dict[str, Any]) -> None:
    path = _profile_path(subject)
    path.parent.mkdir(parents=True, exist_ok=True)
    profile["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# System-Prompt-Generator: NUR verifizierte Fakten
# ---------------------------------------------------------------------------

ANTI_HALLUCINATION_RULES = """
═══════════════════════════════════════════════════════════
⚠️  ABSOLUTE ANTI-HALLUZINATIONS-REGELN — NIEMALS BRECHEN ⚠️
═══════════════════════════════════════════════════════════

1. Du darfst AUSSCHLIESSLICH Aussagen machen, die durch die oben gelisteten FAKTEN belegt sind.
2. Wenn du etwas nicht weißt, sage IMMER: "Das weiß ich leider noch nicht."
   Stelle dann EINE gezielte Folgefrage, um den fehlenden Fakt zu erfahren.
3. ERFINDE NIEMALS:
   - Alter oder Geburtsdaten
   - Namen, Schule, Klasse, Beruf
   - Hobbys, Interessen, Vorlieben
   - Gesundheitsinfo, Charaktereigenschaften
   - Beziehungen oder soziale Details
4. Wenn der Nutzer dir etwas Neues über die Person erzählt, bestätige es und
   antworte, dass du es gespeichert hast (es wird automatisch gespeichert).
5. Bei Widersprüchen: Frage nach, welche Version korrekt ist.
6. KEINE Vermutungen. KEINE Wahrscheinlichkeiten. NUR Fakten oder "Ich weiß es nicht".
═══════════════════════════════════════════════════════════
"""


def build_system_prompt(profile: Dict[str, Any]) -> str:
    display_name = profile.get("display_name", "die Person")
    relation = profile.get("relation_to_sven", "Familienmitglied")
    facts: List[Dict] = profile.get("facts", [])
    unknown: List[Dict] = profile.get("unknown_facts", [])

    facts_section = ""
    if facts:
        facts_section = f"\n\n## ✅ BEKANNTE FAKTEN über {display_name}:\n"
        for f in facts:
            confidence = f.get("confidence", "?")
            marker = "✅" if confidence == "verified" else "⚠️"
            facts_section += f"- {marker} [{f.get('category', '?')}] {f['fact']}\n"
    else:
        facts_section = f"\n\n## ⚠️ BEKANNTE FAKTEN über {display_name}:\nNOCH KEINE FAKTEN GESPEICHERT.\n"

    high_prio_unknown = [q for q in unknown if q.get("priority") == "high"]
    next_question = ""
    if high_prio_unknown:
        q = high_prio_unknown[0]
        next_question = f"\n\nNächste Priorität — Frage nach: {q['question']}"

    return f"""Du bist der persönliche KI-Assistent für {display_name} ({relation} von Sven).
Du kennst {display_name} sehr gut durch die gespeicherten Fakten.
Deine Aufgabe: Helfe {display_name} mit ihren/seinen Anliegen UND lerne sie/ihn besser kennen.
{facts_section}{ANTI_HALLUCINATION_RULES}

## Dein Verhalten wenn Fakten fehlen:
- Sage: "Das weiß ich leider noch nicht, {display_name}."
- Stelle dann diese Frage: {next_question if next_question else 'Frage nach dem nächsten unbekannten Fakt.'}
- Wenn {display_name} etwas erzählt: Bedanke dich, bestätige dass du es speicherst.

## Kommunikationsstil:
- Warm, persönlich, direkt
- Deutsch, duzen
- Kurze, klare Antworten
- Bei Bedarf nachfragen statt annehmen
"""


# ---------------------------------------------------------------------------
# LLM-Aufruf (Ollama + Fallback GitHub Models)
# ---------------------------------------------------------------------------

async def call_llm(messages: List[Dict], model: str = OLLAMA_MODEL) -> str:
    """Ruft Ollama auf, fällt bei Fehler auf GitHub Models zurück."""
    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Ollama nicht erreichbar: {e}")

        if GH_TOKEN:
            try:
                resp = await client.post(
                    f"{GITHUB_MODELS_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {GH_TOKEN}"},
                    json={"model": FALLBACK_MODEL, "messages": messages},
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"GitHub Models Fallback fehlgeschlagen: {e}")

    return "Ich kann gerade keine Verbindung zum KI-Modell aufbauen. Bitte versuche es später erneut."


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


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _extract_learned_facts(reply: str, message: str, subject: str) -> List[str]:
    """Einfaches Heuristik-Parsing um neue Fakten aus dem Nutzer-Input zu extrahieren."""
    learned = []
    keywords_that_signal_fact = [
        "ich bin", "ich habe", "ich mag", "mein", "meine", "ich gehe", "ich lerne",
        "ich spiele", "ich liebe", "ich hasse", "ich wohne", "ich arbeite"
    ]
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in keywords_that_signal_fact):
        learned.append(message[:200])
    return learned


def _get_next_unknown_question(profile: Dict) -> Optional[str]:
    unknowns = profile.get("unknown_facts", [])
    high = [q for q in unknowns if q.get("priority") == "high"]
    medium = [q for q in unknowns if q.get("priority") == "medium"]
    queue = high + medium
    if queue:
        return queue[0].get("question")
    if unknowns:
        return unknowns[0].get("question")
    return None


# ---------------------------------------------------------------------------
# Routen
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    subjects = []
    for subject in ["samira", "sineo"]:
        path = _profile_path(subject)
        if path.exists():
            p = load_profile(subject)
            subjects.append({
                "subject": subject,
                "fact_count": len(p.get("facts", [])),
                "unknown_count": len(p.get("unknown_facts", [])),
            })
    return {"status": "ok", "service": "personal-agents", "version": "1.0.0", "profiles": subjects}


@app.get("/{subject}/profile", response_model=ProfileResponse)
async def get_profile(subject: str):
    """Gibt das vollständige Profil mit allen gespeicherten Fakten zurück."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    unknowns = profile.get("unknown_facts", [])
    high = [q["question"] for q in unknowns if q.get("priority") == "high"]
    med = [q["question"] for q in unknowns if q.get("priority") == "medium"]
    return ProfileResponse(
        subject=subject,
        display_name=profile.get("display_name", subject.capitalize()),
        relation=profile.get("relation_to_sven", "Familienmitglied"),
        fact_count=len(facts),
        unknown_count=len(unknowns),
        facts=[
            FactResponse(
                id=f.get("id", str(uuid.uuid4())[:8]),
                category=f.get("category", "?"),
                fact=f["fact"],
                confidence=f.get("confidence", "verified"),
                learned_at=f.get("learned_at", "unbekannt"),
            )
            for f in facts
        ],
        next_questions=(high + med)[:5],
    )


@app.post("/{subject}/facts", response_model=FactResponse)
async def add_fact(subject: str, fact_data: FactCreate):
    """Speichert einen neuen Fakt über die Person."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    new_id = f"f{len(facts) + 1:03d}"
    new_fact = {
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
    logger.info(f"[{subject}] Neuer Fakt gespeichert: {fact_data.fact[:60]}")
    return FactResponse(
        id=new_id,
        category=new_fact["category"],
        fact=new_fact["fact"],
        confidence=new_fact["confidence"],
        learned_at=new_fact["learned_at"],
    )


@app.delete("/{subject}/facts/{fact_id}")
async def delete_fact(subject: str, fact_id: str):
    """Löscht einen Fakt (z.B. weil er falsch war)."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    original_len = len(facts)
    profile["facts"] = [f for f in facts if f.get("id") != fact_id]
    if len(profile["facts"]) == original_len:
        raise HTTPException(404, f"Fakt '{fact_id}' nicht gefunden")
    save_profile(subject, profile)
    return {"deleted": fact_id}


@app.delete("/{subject}/unknown/{question_id}")
async def resolve_unknown(subject: str, question_id: str):
    """Markiert eine offene Frage als beantwortet (entfernt sie aus der Liste)."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    unknowns = profile.get("unknown_facts", [])
    profile["unknown_facts"] = [q for q in unknowns if q.get("id") != question_id]
    save_profile(subject, profile)
    return {"resolved": question_id}


@app.get("/{subject}/interview")
async def get_interview_questions(subject: str, limit: int = 5):
    """Gibt die nächsten Fragen zurück, die der Agent stellen sollte."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    unknowns = profile.get("unknown_facts", [])
    high = [q for q in unknowns if q.get("priority") == "high"]
    medium = [q for q in unknowns if q.get("priority") == "medium"]
    low = [q for q in unknowns if q.get("priority") == "low"]
    queue = (high + medium + low)[:limit]
    return {
        "subject": subject,
        "display_name": profile.get("display_name"),
        "total_unknown": len(unknowns),
        "next_questions": [q["question"] for q in queue],
        "fact_count": len(profile.get("facts", [])),
        "profile_complete_pct": round(
            len(profile.get("facts", [])) /
            max(len(profile.get("facts", [])) + len(unknowns), 1) * 100, 1
        ),
    }


@app.post("/{subject}/chat", response_model=ChatResponse)
async def chat_with_agent(subject: str, request: ChatRequest):
    """
    Fakten-basierter Chat mit dem persönlichen Agenten.

    GARANTIE: Alle Antworten basieren NUR auf gespeicherten Fakten.
    Unbekannte Fakten → Agent fragt nach statt zu erfinden.
    """
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")

    profile = load_profile(subject)
    system_prompt = build_system_prompt(profile)

    messages = [{"role": "system", "content": system_prompt}]
    if request.conversation_history:
        messages.extend(request.conversation_history[-10:])  # letzten 10 Turns
    messages.append({"role": "user", "content": request.message})

    reply = await call_llm(messages)

    # Auto-Fakten aus Nutzer-Nachricht extrahieren
    new_facts = _extract_learned_facts(reply, request.message, subject)
    saved_facts = []
    for raw_fact in new_facts:
        facts = profile.get("facts", [])
        new_id = f"f{len(facts) + 1:03d}"
        profile.setdefault("facts", []).append({
            "id": new_id,
            "category": "auto-learned",
            "fact": raw_fact,
            "confidence": "inferred",
            "source": "conversation",
            "learned_at": datetime.now().strftime("%Y-%m-%d"),
        })
        saved_facts.append(raw_fact)

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


@app.get("/{subject}/intro")
async def introduce_agent(subject: str):
    """Der Agent stellt sich und die bekannten Fakten über die Person vor."""
    if subject not in ("samira", "sineo"):
        raise HTTPException(404, "Unbekanntes Profil")
    profile = load_profile(subject)
    facts = profile.get("facts", [])
    name = profile.get("display_name", subject.capitalize())
    unknowns = profile.get("unknown_facts", [])
    high_q = [q["question"] for q in unknowns if q.get("priority") == "high"]

    intro = (
        f"Hallo! Ich bin der persönliche Assistent für {name}. "
        f"Ich kenne aktuell {len(facts)} Fakt(en) über {name}. "
    )
    if not facts:
        intro += (
            f"Ich lerne {name} gerade erst kennen. "
            f"Um gut helfen zu können, würde ich gerne wissen: "
            + (high_q[0] if high_q else "Magst du mir etwas über dich erzählen?")
        )
    else:
        intro += f"Ich helfe {name} bei allem was ich kann — basierend auf dem was ich über sie/ihn weiß."
        if high_q:
            intro += f" Ich würde noch gerne wissen: {high_q[0]}"

    return {
        "subject": subject,
        "display_name": name,
        "intro": intro,
        "known_facts": len(facts),
        "unknown_facts": len(unknowns),
        "next_question": high_q[0] if high_q else None,
        "profile_complete_pct": round(
            len(facts) / max(len(facts) + len(unknowns), 1) * 100, 1
        ),
    }
