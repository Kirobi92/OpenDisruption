"""
agents/hermes/agent.py — Hermes-Reasoner-Agent mit echtem LLM-Reasoning

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Multi-Step-Reasoning, Chain-of-Thought
  - Pro/Contra-Debatte
  - Hypothesen-Generierung + Validierung
  - Research-Synthese (Multi-Source)
  - Dokument-Verarbeitung aus sources/inbox/ (PDF, TXT, MD, JSON)

Erlaubte Zonen: PUBLIC, WORKSPACE (Input & Output)

Hinweis: Dieser Agent heißt intern "hermes-reasoner" um Kollision mit
dem bestehenden "hermes-extractor" zu vermeiden (siehe MULTI-AGENT-ARCHITECTURE.md §3.1).

Zone: WORKSPACE
Autor: kirobi-coder
Version: 2.0 (Phase 4 — echtes LLM-Reasoning via Ollama)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from agents._base.agent import BaseAgent, AgentResult, Task

logger = logging.getLogger(__name__)

# ─── Ollama-Konfiguration ─────────────────────────────────────────────────────

_DEFAULT_OLLAMA_HOST = "http://ollama:11434"
_DEFAULT_MODEL = "llama3.2"
_OLLAMA_TIMEOUT = 60.0  # Sekunden

# ─── Keyword-Fallback für Zone-Klassifikation ─────────────────────────────────

_ZONE_KEYWORDS: dict[str, list[str]] = {
    "SACRED": [
        "trauma", "therapie", "missbrauch", "gewalt", "suizid", "depression",
        "angst", "panik", "seele", "sacred", "geheim", "vertraulich",
        "abuse", "therapy", "suicide", "secret", "confidential",
    ],
    "FAMILY_PRIVATE": [
        "familie", "kind", "kinder", "eltern", "mama", "papa", "oma", "opa",
        "hochzeit", "geburtstag", "urlaub", "zuhause", "privat",
        "family", "child", "children", "parents", "wedding", "birthday",
        "vacation", "home", "private",
    ],
    "QUARANTINE": [
        "unbekannt", "ungeprüft", "extern", "import", "upload",
        "unknown", "unverified", "external", "imported",
    ],
    "PUBLIC": [
        "öffentlich", "veröffentlichung", "blog", "artikel", "news",
        "public", "publication", "press", "release", "announcement",
    ],
}


def _keyword_classify(text: str) -> tuple[str, float]:
    """Keyword-basierte Zone-Klassifikation als Fallback.

    Returns:
        Tuple aus (zone, confidence) — confidence ist niedrig (0.3–0.5)
        um anzuzeigen dass dies ein Fallback ist.
    """
    text_lower = text.lower()
    scores: dict[str, int] = {zone: 0 for zone in _ZONE_KEYWORDS}

    for zone, keywords in _ZONE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[zone] += 1

    best_zone = max(scores, key=lambda z: scores[z])
    best_score = scores[best_zone]

    if best_score == 0:
        return "WORKSPACE", 0.3

    # Confidence proportional zur Anzahl Treffer, max 0.5 (Fallback-Deckel)
    confidence = min(0.3 + best_score * 0.05, 0.5)
    return best_zone, confidence


def _extract_text_from_file(file_path: Path) -> str:
    """Extrahiert Text aus einer Datei (TXT, MD, JSON, PDF-Stub).

    PDF-Unterstützung erfordert pypdf/pdfminer — falls nicht verfügbar,
    wird ein lesbarer Hinweis zurückgegeben.
    """
    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8", errors="replace")

    if suffix == ".json":
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw)
            # Kompaktes JSON als Text für LLM
            return json.dumps(data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return raw

    if suffix == ".pdf":
        try:
            import importlib
            pypdf = importlib.import_module("pypdf")
            reader = pypdf.PdfReader(str(file_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except ImportError:
            pass
        try:
            pdfminer_high = importlib.import_module("pdfminer.high_level")
            return pdfminer_high.extract_text(str(file_path))
        except ImportError:
            return f"[PDF-Datei: {file_path.name} — kein PDF-Parser verfügbar]"

    # Unbekanntes Format: als Text versuchen
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[Lesefehler: {exc}]"


def _build_classification_prompt(text: str, filename: str) -> str:
    """Erstellt den Prompt für die LLM-Klassifikation."""
    # Text auf 3000 Zeichen kürzen um Token-Limit zu respektieren
    truncated = text[:3000]
    if len(text) > 3000:
        truncated += "\n\n[... Text gekürzt ...]"

    return f"""Du bist ein Dokumenten-Klassifikations-Assistent für das Kirobi-System.

Analysiere das folgende Dokument und erstelle:
1. Eine kurze Zusammenfassung (2-4 Sätze)
2. Eine Zone-Klassifikation nach dem Kirobi-Sicherheitsmodell
3. Relevante Tags (3-7 Stichworte)
4. Einen Konfidenzwert (0.0 bis 1.0)

## Zonen-Definitionen:
- PUBLIC: Öffentlich teilbar, keine persönlichen Daten
- WORKSPACE: Interne Arbeits-/Technikdokumente, nicht persönlich
- FAMILY_PRIVATE: Familiäre oder persönliche Inhalte
- QUARANTINE: Ungeprüfte, externe oder potenziell unsichere Inhalte
- SACRED: Hochsensibel, nur für Sven (Trauma, tiefste Werte, Grenzen)

## Dokument: {filename}

{truncated}

## Antwort (NUR valides JSON, keine Erklärungen außerhalb):
{{
  "summary": "...",
  "zone": "WORKSPACE",
  "tags": ["tag1", "tag2"],
  "confidence": 0.85
}}"""


async def _call_ollama(
    prompt: str,
    *,
    ollama_host: str,
    model: str,
) -> dict[str, Any]:
    """Ruft die Ollama-API async auf und gibt das geparste JSON zurück.

    Raises:
        RuntimeError: Wenn Ollama nicht erreichbar oder Antwort ungültig.
    """
    try:
        import httpx
    except ImportError as exc:
        raise RuntimeError("httpx nicht installiert — Ollama-Call nicht möglich") from exc

    url = f"{ollama_host.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Niedrig für konsistente Klassifikation
            "num_predict": 512,
        },
    }

    async with httpx.AsyncClient(timeout=_OLLAMA_TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_text: str = data.get("response", "")

    # JSON aus der Antwort extrahieren (LLM kann Markdown-Blöcke erzeugen)
    json_match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
    if not json_match:
        raise RuntimeError(f"Kein JSON in Ollama-Antwort gefunden: {raw_text[:200]!r}")

    result = json.loads(json_match.group())

    # Pflichtfelder validieren
    required = {"summary", "zone", "tags", "confidence"}
    missing = required - result.keys()
    if missing:
        raise RuntimeError(f"Fehlende Felder in LLM-Antwort: {missing}")

    # Zone validieren
    valid_zones = {"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"}
    if result["zone"] not in valid_zones:
        logger.warning(
            "LLM hat ungültige Zone '%s' zurückgegeben — fallback auf QUARANTINE",
            result["zone"],
        )
        result["zone"] = "QUARANTINE"

    # Confidence auf [0.0, 1.0] klemmen
    result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))

    return result


async def _process_document_async(
    file_path: Path,
    *,
    ollama_host: str,
    model: str,
) -> dict[str, Any]:
    """Verarbeitet ein Dokument async: Text extrahieren → LLM → Ergebnis.

    Bei Ollama-Fehler: graceful fallback auf keyword-basierte Klassifikation.
    """
    text = _extract_text_from_file(file_path)
    filename = file_path.name

    if not text.strip():
        return {
            "summary": f"Leeres Dokument: {filename}",
            "zone": "QUARANTINE",
            "tags": ["empty", "no-content"],
            "confidence": 0.1,
            "llm_used": False,
            "fallback_reason": "empty_document",
        }

    prompt = _build_classification_prompt(text, filename)

    try:
        result = await _call_ollama(prompt, ollama_host=ollama_host, model=model)
        result["llm_used"] = True
        result["fallback_reason"] = None
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Ollama nicht erreichbar oder Fehler (%s) — verwende Keyword-Fallback",
            exc,
        )
        zone, confidence = _keyword_classify(text)
        # Einfache Zusammenfassung aus erstem Absatz
        first_para = text.strip().split("\n\n")[0][:300].strip()
        return {
            "summary": first_para if first_para else f"Dokument: {filename}",
            "zone": zone,
            "tags": ["fallback", "keyword-classified"],
            "confidence": confidence,
            "llm_used": False,
            "fallback_reason": str(exc),
        }


class HermesReasonerAgent(BaseAgent):
    """
    Reasoning-Agent: Logik, Debatte, Hypothesen, Synthese, Dokument-Klassifikation.

    Unterstützte Task-Typen:
    - ``chain_of_thought``: Schrittweise Schlussfolgerung via LLM
    - ``debate``: Pro/Contra-Analyse
    - ``hypothesis``: Hypothesen-Generierung und Validierung
    - ``research_synthesis``: Zusammenführung mehrerer Quellen
    - ``multi_step_reasoning``: Mehrstufige Problemlösung
    - ``classify_document``: Dokument aus sources/inbox/ klassifizieren

    Headless-Aufruf (sync):
        agent = HermesReasonerAgent()
        result = agent.run(Task(
            task_type="classify_document",
            payload={"file_path": "sources/inbox/doc.pdf"}
        ))

    Headless-Aufruf (async):
        agent = HermesReasonerAgent()
        result = await agent.handle_async(Task(
            task_type="chain_of_thought",
            payload={"question": "Warum ist Rust schneller als Python?"}
        ))
    """

    agent_id = "hermes-reasoner"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE"})

    KNOWN_TASK_TYPES = frozenset({
        "chain_of_thought",
        "debate",
        "hypothesis",
        "research_synthesis",
        "multi_step_reasoning",
        "classify_document",
    })

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._ollama_host: str = os.getenv("OLLAMA_HOST", _DEFAULT_OLLAMA_HOST)
        self._model: str = os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)

    # ─── Sync-Wrapper (BaseAgent-Interface) ───────────────────────────────────

    def handle(self, task: Task) -> AgentResult:
        """Sync-Wrapper: delegiert an ``handle_async`` via asyncio."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # In einem laufenden Event-Loop: neuen Thread nutzen
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self.handle_async(task))
                return future.result()
        else:
            return asyncio.run(self.handle_async(task))

    # ─── Async-Hauptlogik ─────────────────────────────────────────────────────

    async def handle_async(self, task: Task) -> AgentResult:
        """Async-Hauptlogik: dispatcht nach task_type."""
        task_type = task.task_type

        if task_type == "classify_document":
            return await self._handle_classify_document(task)

        # Alle anderen Reasoning-Task-Typen: LLM-Reasoning
        return await self._handle_reasoning(task)

    # ─── Task-Handler ─────────────────────────────────────────────────────────

    async def _handle_classify_document(self, task: Task) -> AgentResult:
        """Klassifiziert ein Dokument aus sources/inbox/."""
        file_path_str: str | None = task.payload.get("file_path")
        if not file_path_str:
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error="Pflichtfeld 'file_path' fehlt im Payload",
                confidence=0.0,
            )

        file_path = Path(file_path_str)
        if not file_path.exists():
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=f"Datei nicht gefunden: {file_path}",
                confidence=0.0,
            )

        result_data = await _process_document_async(
            file_path,
            ollama_host=self._ollama_host,
            model=self._model,
        )

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "summary": result_data["summary"],
                "zone": result_data["zone"],
                "tags": result_data["tags"],
                "confidence": result_data["confidence"],
                "llm_used": result_data.get("llm_used", False),
                "fallback_reason": result_data.get("fallback_reason"),
                "file_path": str(file_path),
                "filename": file_path.name,
            },
            confidence=result_data["confidence"],
        )

    def _extract_question(self, task: Task) -> str:
        """Extrahiert die Hauptfrage aus dem Payload — task-typ-spezifisch.

        Jeder Task-Typ hat sein eigenes primäres Payload-Feld:
        - chain_of_thought / multi_step_reasoning: ``question``
        - debate: ``topic``
        - hypothesis: ``claim``
        - research_synthesis: ``sources`` (Liste → wird zu Frage)
        Fallback: leerer String (graceful degradation via Ollama-Offline-Pfad).
        """
        p = task.payload
        tt = task.task_type
        if tt == "debate":
            return p.get("topic") or p.get("question", "")
        if tt == "hypothesis":
            return p.get("claim") or p.get("question", "")
        if tt == "research_synthesis":
            sources = p.get("sources", [])
            if isinstance(sources, list):
                return p.get("question") or f"Synthese aus {len(sources)} Quellen: {', '.join(str(s) for s in sources[:3])}"
            return p.get("question", str(sources))
        # chain_of_thought, multi_step_reasoning, unbekannte Typen
        return p.get("question", "")

    async def _handle_reasoning(self, task: Task) -> AgentResult:
        """Führt LLM-Reasoning für Chain-of-Thought, Debate, etc. durch."""
        question: str = self._extract_question(task)
        context: str = task.payload.get("context", "")
        task_type = task.task_type

        prompt = self._build_reasoning_prompt(task_type, question, context)

        try:
            raw_result = await _call_ollama(
                prompt,
                ollama_host=self._ollama_host,
                model=self._model,
            )
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=True,
                payload={
                    "question": question,
                    "task_type": task_type,
                    "summary": raw_result.get("summary", ""),
                    "reasoning_steps": raw_result.get("reasoning_steps", []),
                    "conclusion": raw_result.get("conclusion"),
                    "tags": raw_result.get("tags", []),
                    "confidence": raw_result.get("confidence", 0.0),
                    "llm_used": True,
                    "fallback_reason": None,
                },
                confidence=raw_result.get("confidence", 0.0),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama-Reasoning fehlgeschlagen: %s", exc)
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=True,  # Graceful degradation
                payload={
                    "question": question,
                    "task_type": task_type,
                    "summary": f"Reasoning nicht verfügbar (Ollama offline): {question}",
                    "reasoning_steps": [],
                    "conclusion": None,
                    "sources": [],
                    "tags": ["fallback", "ollama-offline"],
                    "confidence": 0.1,
                    "llm_used": False,
                    "fallback_reason": str(exc),
                },
                confidence=0.1,
            )

    def _build_reasoning_prompt(
        self, task_type: str, question: str, context: str
    ) -> str:
        """Erstellt einen task-typ-spezifischen Reasoning-Prompt."""
        context_block = f"\n\n## Kontext:\n{context}" if context else ""

        type_instructions = {
            "chain_of_thought": (
                "Denke Schritt für Schritt. Liste deine Reasoning-Schritte auf "
                "und komme zu einer klaren Schlussfolgerung."
            ),
            "debate": (
                "Analysiere Pro- und Contra-Argumente. Sei ausgewogen und "
                "berücksichtige verschiedene Perspektiven."
            ),
            "hypothesis": (
                "Generiere testbare Hypothesen. Beschreibe wie jede Hypothese "
                "validiert oder falsifiziert werden könnte."
            ),
            "research_synthesis": (
                "Synthetisiere die Informationen aus verschiedenen Quellen. "
                "Identifiziere Gemeinsamkeiten, Widersprüche und Lücken."
            ),
            "multi_step_reasoning": (
                "Löse das Problem in mehreren klar definierten Schritten. "
                "Jeder Schritt soll auf dem vorherigen aufbauen."
            ),
        }

        instruction = type_instructions.get(
            task_type,
            "Analysiere die Frage gründlich und gib eine strukturierte Antwort.",
        )

        return f"""Du bist ein Reasoning-Assistent im Kirobi-System.

## Aufgabe ({task_type}):
{instruction}

## Frage:
{question}{context_block}

## Antwort (NUR valides JSON):
{{
  "summary": "Kurze Zusammenfassung der Antwort",
  "reasoning_steps": ["Schritt 1...", "Schritt 2...", "Schritt 3..."],
  "conclusion": "Finale Schlussfolgerung",
  "tags": ["tag1", "tag2"],
  "confidence": 0.85
}}"""
