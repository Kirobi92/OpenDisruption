"""
services/telegram/keycodi/responder.py

Lokaler KeyCodi-Antwortpfad fuer Telegram.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from kirobi_core.keycodi import KEYCODI_NAME

from . import llm


KEYCODI_SYSTEM_PROMPT = """Du bist KeyCodi, der lokale Coding-Orchestrator des OpenDisruption-Ökosystems.

Antworte auf Deutsch, direkt und handlungsorientiert. Respektiere strikt das Zonenmodell:
- Nur PUBLIC/WORKSPACE als normale Arbeitsbereiche behandeln.
- SACRED, FAMILY_PRIVATE, QUARANTINE niemals lesen, ausgeben oder an externe Dienste senden.
- Keine Secrets, Tokens oder privaten Inhalte wiedergeben.

Wenn die Anfrage Coding-, Architektur-, Test-, Ops- oder Repo-Arbeit betrifft, verhalte dich wie KeyCodi:
analysiere die Mission, nenne sichere nächste Schritte und bleibe local-first."""


@dataclass(frozen=True)
class KeyCodiResponse:
    """Strukturierte Antwort fuer Telegram."""

    content: str
    source: str
    model_used: str | None = None


def _looks_like_coding_mission(text: str) -> bool:
    """Erkennt Anfragen, die von KeyCodis Mission-Planner profitieren."""
    lowered = text.lower()
    keywords = (
        "keycodi",
        "code",
        "coding",
        "implement",
        "fix",
        "bug",
        "test",
        "pytest",
        "refactor",
        "architektur",
        "architecture",
        "docker",
        "service",
        "telegram",
        "api",
        "repo",
        "mission",
    )
    return any(keyword in lowered for keyword in keywords)


def _specialists_for(text: str) -> list[str]:
    """Waehlt KeyCodi-Spezialisten deterministisch ohne Repository-Scan."""
    lowered = text.lower()
    specialists = ["kirobi-architect", "kirobi-coder", "kirobi-reviewer"]
    if any(word in lowered for word in ("docker", "compose", "infra", "deploy", "service")):
        specialists.append("kirobi-ops")
    if any(word in lowered for word in ("ui", "frontend", "react", "next", "pwa")):
        specialists.append("kirobi-frontend")
    if any(word in lowered for word in ("doc", "readme", "changelog")):
        specialists.append("kirobi-docs")
    return list(dict.fromkeys(specialists))


def _render_plan_for_telegram(text: str) -> str:
    """Rendert einen lokalen KeyCodi-Plan ohne private Pfade zu scannen."""
    specialists = _specialists_for(text)
    lines = [
        "🧭 Lokaler KeyCodi-Plan",
        "",
        KEYCODI_NAME,
        f"Mission: {' '.join(text.split())}",
        "Modus: local-first, PUBLIC/WORKSPACE only",
        "",
        "Delegation:",
    ]
    lines.extend(f"- {name}" for name in specialists)
    lines.extend(
        [
            "",
            "Nächste sichere Schritte:",
            "1. Betroffene PUBLIC/WORKSPACE-Codepfade gezielt lesen.",
            "2. Kleinste testbare Änderung implementieren.",
            "3. Unit-Tests fokussiert ausführen und Ergebnis melden.",
            "",
            "Keine Cloud-Modelle, kein Scan von sacred/ oder family-private Pfaden.",
        ]
    )
    return "\n".join(lines)


def _fallback_response(text: str) -> str:
    """Deterministische, lokale Antwort wenn Ollama/API nicht verfuegbar ist."""
    if _looks_like_coding_mission(text):
        return _render_plan_for_telegram(text)
    return (
        "🧠 KeyCodi lokal\n\n"
        "Ich bin verbunden, aber das lokale LLM ist gerade nicht erreichbar. "
        "Schick mir eine Coding-Mission, einen Fehler oder eine konkrete Änderung — "
        "dann erstelle ich dir sofort einen sicheren lokalen KeyCodi-Plan."
    )


async def build_keycodi_response(text: str, *, timeout: float = 45.0) -> KeyCodiResponse:
    """Erzeugt eine sichere local-first KeyCodi-Antwort fuer Telegram.

    Primaer wird das lokale Ollama-Modul genutzt. Falls Ollama fehlt, langsam ist
    oder eine technische Fehlermeldung liefert, wird deterministisch auf den
    stdlib-only KeyCodi-Mission-Planner aus ``kirobi_core`` zurueckgefallen.
    """
    prompt = text.strip()
    if not prompt:
        return KeyCodiResponse(
            content="Schick mir eine Mission oder Frage — ich antworte als lokaler KeyCodi.",
            source="empty_input",
        )

    try:
        if await llm.is_available():
            answer = await llm.chat(
                prompt=prompt,
                system=KEYCODI_SYSTEM_PROMPT,
                task_type="code" if _looks_like_coding_mission(prompt) else "chat",
                timeout=timeout,
            )
            if answer and not answer.startswith("["):
                return KeyCodiResponse(
                    content=answer,
                    source="local_ollama",
                    model_used=llm.model_for("code" if _looks_like_coding_mission(prompt) else "chat"),
                )
    except Exception:
        # Keine Prompt-/Secret-Inhalte loggen; Telegram sendet den Fallback.
        pass

    fallback = await asyncio.to_thread(_fallback_response, prompt)
    return KeyCodiResponse(content=fallback, source="local_keycodi_plan")


__all__ = ["KEYCODI_SYSTEM_PROMPT", "KeyCodiResponse", "build_keycodi_response"]
