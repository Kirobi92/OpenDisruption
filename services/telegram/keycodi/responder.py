"""
services/telegram/keycodi/responder.py

Lokaler Telegram-Antwortpfad mit KeyCodi als Primaerroute.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from . import llm


KEYCODI_SYSTEM_PROMPT = """Du bist KeyCodi, der Master-Code-Orchestrator des OpenDisruption-Ökosystems von Sven.

Du bist kein Placeholder-Bot. Du sprichst mit Sven direkt, warm, präzise und auf Augenhöhe.
Antworte auf Deutsch, konkret und handlungsorientiert. Respektiere strikt das Zonenmodell:
- Nur PUBLIC/WORKSPACE als normale Arbeitsbereiche behandeln.
- SACRED, FAMILY_PRIVATE, QUARANTINE niemals lesen, ausgeben oder an externe Dienste senden.
- Keine Secrets, Tokens oder privaten Inhalte wiedergeben.

Wenn die Anfrage Coding-, Architektur-, Test-, Ops- oder Repo-Arbeit betrifft, verhalte dich als KeyCodi:
analysiere die Mission, nenne sichere nächste Schritte, delegiere gedanklich an Spezialisten und bleibe local-first."""

COPILOT_SYSTEM_PROMPT = """Du bist GitHub Copilot im OpenDisruption-Repository.

Antworte auf Deutsch, präzise, technisch und umsetzungsorientiert. Fokus:
- Repo-Verständnis, Architektur, Code, Tests, Services, Deployments
- klare nächste Schritte statt generischer Menü-Erklärungen
- niemals Secrets, Tokens oder private Inhalte ausgeben
- SACRED, FAMILY_PRIVATE und QUARANTINE nicht lesen, nicht zitieren, nicht nach außen geben

Wenn möglich, formuliere konkret in Bezug auf die bestehende Codebasis und auf produktive Umsetzbarkeit."""


@dataclass(frozen=True)
class KeyCodiResponse:
    """Strukturierte Antwort fuer Telegram."""

    content: str
    source: str
    model_used: str | None = None


def _keycodi_task_type_for(text: str) -> str:
    """Leitet den passenden KeyCodi-Task-Typ grob aus der Frage ab."""
    lowered = text.lower()
    if any(word in lowered for word in ("pro und contra", "vor- und nachteile", "compare", "vs", "versus")):
        return "debate"
    if any(word in lowered for word in ("hypothese", "hypothesis", "vermute", "annahme")):
        return "hypothesis"
    if any(word in lowered for word in ("synthese", "zusammenführen", "combine sources", "quellen")):
        return "research_synthesis"
    if any(word in lowered for word in ("schritt", "plan", "debug", "analys", "warum", "how", "wie")):
        return "multi_step_reasoning"
    return "chain_of_thought"


def _render_hermes_content(payload: dict[str, object]) -> str:
    """Formatiert Hermes-Reasoning kompakt und telegram-tauglich."""
    summary = str(payload.get("summary") or "").strip()
    conclusion = str(payload.get("conclusion") or "").strip()
    steps = payload.get("reasoning_steps")
    reasoning_steps = [str(step).strip() for step in steps if str(step).strip()] if isinstance(steps, list) else []

    parts: list[str] = []
    if summary:
        parts.append(summary)
    if conclusion and conclusion != summary:
        if parts:
            parts.append("")
        parts.append(f"Schlussfolgerung: {conclusion}")
    if reasoning_steps:
        if parts:
            parts.append("")
        parts.append("Zwischenschritte:")
        for index, step in enumerate(reasoning_steps[:3], start=1):
            parts.append(f"{index}. {step}")
    return "\n".join(parts).strip()


async def _build_keycodi_llm_response(
    text: str,
    *,
    context: str = "",
    timeout: float = 45.0,
    persona: str = "hermes",
) -> KeyCodiResponse | None:
    """Versucht eine echte KeyCodi-Antwort über den aktiven LLM-Pfad zu erzeugen."""
    if not await llm.is_available():
        return None

    reasoning_mode = _keycodi_task_type_for(text)
    if persona == "copilot":
        task_type = "code" if _looks_like_coding_mission(text) else "chat"
        system_prompt = COPILOT_SYSTEM_PROMPT
        intro = (
            "Du antwortest im Telegram-Chat als Copilot für Sven. "
            "Sei konkret, repo-nah und technisch hilfreich. "
            "Nutze nur PUBLIC/WORKSPACE-Inhalte."
        )
        source = "copilot_cloud"
    else:
        task_type = "code" if _looks_like_coding_mission(text) else "chat"
        system_prompt = KEYCODI_SYSTEM_PROMPT
        intro = (
            "Du antwortest im Telegram-Chat als KeyCodi fuer Sven. "
            "Antworte nicht wie ein Menü und nicht wie ein Placeholder. "
            "Sei konkret, handlungsorientiert und local-first. "
            "Nutze nur PUBLIC/WORKSPACE-Inhalte."
        )
        source = "keycodi_local"

    telegram_context = intro
    if context:
        telegram_context = f"{telegram_context}\n\nBisheriger Chatverlauf:\n{context}"
    prompt = (
        f"Modus: {reasoning_mode}\n\n"
        f"Anfrage von Sven:\n{text}\n\n"
        "Antworte mit klarer Analyse, nächstem Schritt und, wenn sinnvoll, "
        "kompakten Zwischenschritten."
    )

    answer = await llm.chat(
        prompt=prompt,
        system=system_prompt + "\n\n" + telegram_context,
        task_type=task_type,
        timeout=timeout,
    )
    if not answer or answer.startswith("["):
        return None

    return KeyCodiResponse(
        content=answer.strip(),
        source=source,
        model_used=llm.model_for(task_type),
    )


def _looks_like_coding_mission(text: str) -> bool:
    """Erkennt Anfragen, die vom lokalen Fallback-Plan profitieren."""
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
    """Waehlt lokale Spezialisten deterministisch ohne Repository-Scan."""
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
    """Rendert einen lokalen Hermes-Fallback-Plan ohne private Pfade zu scannen."""
    specialists = _specialists_for(text)
    lines = [
        "🧭 Lokaler KeyCodi-Fallback-Plan",
        "",
        "KeyCodi — Master-Code-Orchestrator",
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
    """Deterministische Antwort wenn kein Modellpfad verfügbar ist."""
    if _looks_like_coding_mission(text):
        return _render_plan_for_telegram(text)
    return (
        "🧠 KeyCodi lokal\n\n"
        "Ich bin verbunden, aber mein Modellpfad ist gerade nicht erreichbar. "
        "Schick mir eine Coding-Mission, einen Fehler oder eine konkrete Änderung — "
        "dann erstelle ich dir sofort einen sicheren KeyCodi-Fallback-Plan."
    )


async def build_keycodi_response(text: str, *, timeout: float = 45.0) -> KeyCodiResponse:
    """Erzeugt eine sichere local-first Telegram-Antwort.

    Prioritaet:
    1. KeyCodi über den echten lokalen LLM-Pfad
    2. Deterministischer lokaler KeyCodi-Fallback-Plan
    """
    return await build_keycodi_response_with_context(text, context="", timeout=timeout)


async def build_keycodi_response_with_context(
    text: str,
    *,
    context: str = "",
    timeout: float = 45.0,
    persona: str = "hermes",
) -> KeyCodiResponse:
    """Wie ``build_keycodi_response()``, aber mit optionalem Chat-Kontext."""
    prompt = text.strip()
    if not prompt:
        return KeyCodiResponse(
            content="Schick mir eine Mission oder Frage — ich antworte direkt aus dem Repo-Kontext.",
            source="empty_input",
        )

    try:
        keycodi_response = await _build_keycodi_llm_response(
            prompt,
            context=context,
            timeout=timeout,
            persona=persona,
        )
        if keycodi_response is not None:
            return keycodi_response
    except Exception:
        # Keine Prompt-/Secret-Inhalte loggen; Telegram sendet den Fallback.
        pass

    fallback = await asyncio.to_thread(_fallback_response, prompt)
    return KeyCodiResponse(content=fallback, source="local_keycodi_plan")


__all__ = [
    "KEYCODI_SYSTEM_PROMPT",
    "KeyCodiResponse",
    "build_keycodi_response",
    "build_keycodi_response_with_context",
]
