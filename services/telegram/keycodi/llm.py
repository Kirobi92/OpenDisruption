"""
services/telegram/keycodi/llm.py
LLM-Anbindung für die Telegram-Bots.

Unterstützte Provider:
  - github: GitHub Models / Copilot-nahe Cloud-Modelle
  - ollama: lokale Modelle via Ollama
  - auto: bleibt privacy-safe lokal und nutzt Ollama
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Optional

import httpx

from .config import (
    GITHUB_CHAT_MODEL,
    GITHUB_CODE_MODEL,
    GITHUB_MODELS_TOKEN,
    GITHUB_MODELS_URL,
    GITHUB_REASONING_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_CODE_MODEL,
    MAX_PARALLEL_LOCAL_AGENTS,
)

log = logging.getLogger("keycodi.llm")

# Semaphore: max. 4 gleichzeitige LLM-Requests (entspricht OLLAMA_NUM_PARALLEL)
_sem = asyncio.Semaphore(MAX_PARALLEL_LOCAL_AGENTS)

# Modell-Routing: Aufgaben-Typ → bevorzugtes Modell je Provider
OLLAMA_MODEL_ROUTING: dict[str, str] = {
    "code": OLLAMA_CODE_MODEL,
    "reasoning": "deepseek-r1:32b",
    "chat": OLLAMA_DEFAULT_MODEL,
    "status": OLLAMA_DEFAULT_MODEL,
    "summary": OLLAMA_DEFAULT_MODEL,
    "embedding": "nomic-embed-text",
}

GITHUB_MODEL_ROUTING: dict[str, str] = {
    "code": GITHUB_CODE_MODEL,
    "reasoning": GITHUB_REASONING_MODEL,
    "chat": GITHUB_CHAT_MODEL,
    "status": GITHUB_CHAT_MODEL,
    "summary": GITHUB_CHAT_MODEL,
}


def provider() -> str:
    """Ermittelt den aktiven LLM-Provider."""
    configured = LLM_PROVIDER
    if configured in {"github", "ollama"}:
        return configured
    # Privacy-first: Token-Präsenz darf niemals automatisch Cloud-Nutzung
    # auslösen. GitHub Models nur bei explizitem LLM_PROVIDER=github.
    return "ollama"


def model_for(task_type: str) -> str:
    """Liefert das bevorzugte Modell für den aktiven Provider."""
    if provider() == "github":
        return GITHUB_MODEL_ROUTING.get(task_type, GITHUB_CHAT_MODEL)
    return OLLAMA_MODEL_ROUTING.get(task_type, OLLAMA_DEFAULT_MODEL)


async def _chat_github_models(
    prompt: str,
    *,
    system: str,
    resolved_model: str,
    timeout: float,
) -> str:
    if not GITHUB_MODELS_TOKEN:
        return "[LLM-Fehler: GitHub Models Token fehlt]"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_MODELS_TOKEN}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "model": resolved_model,
        "messages": messages,
        "stream": False,
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(GITHUB_MODELS_URL, headers=headers, json=payload)
        if r.status_code != 200:
            log.warning("GitHub Models %s HTTP %s", resolved_model, r.status_code)
            return f"[LLM-Fehler: HTTP {r.status_code}]"
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return "[LLM-Fehler: Leere GitHub-Models-Antwort]"
        content = choices[0].get("message", {}).get("content", "")
        return content or "[Leere Antwort]"
    except httpx.TimeoutException:
        log.warning("GitHub Models Timeout nach %.0fs für Modell %s", timeout, resolved_model)
        return f"[Timeout nach {timeout:.0f}s — Modell {resolved_model} zu langsam]"
    except Exception as exc:
        log.error("GitHub Models Fehler: %s", exc)
        return f"[LLM-Fehler: {exc}]"


async def _chat_ollama(
    prompt: str,
    *,
    system: str,
    resolved_model: str,
    timeout: float,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": resolved_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_ctx": 8192,
                        "num_thread": 6,
                        "num_gpu": 99,
                    },
                },
            )
        if r.status_code != 200:
            log.warning("Ollama %s HTTP %s", resolved_model, r.status_code)
            return f"[LLM-Fehler: HTTP {r.status_code}]"
        return r.json().get("message", {}).get("content", "[Leere Antwort]")
    except httpx.TimeoutException:
        log.warning("Ollama Timeout nach %.0fs für Modell %s", timeout, resolved_model)
        return f"[Timeout nach {timeout:.0f}s — Modell {resolved_model} zu langsam]"
    except Exception as exc:
        log.error("Ollama Fehler: %s", exc)
        return f"[LLM-Fehler: {exc}]"


async def chat(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    task_type: str = "chat",
    timeout: float = 120.0,
) -> str:
    """Einfacher Chat-Call — gibt die vollständige Antwort zurück."""
    resolved_model = model or model_for(task_type)

    async with _sem:
        if provider() == "github":
            return await _chat_github_models(
                prompt,
                system=system,
                resolved_model=resolved_model,
                timeout=timeout,
            )
        return await _chat_ollama(
            prompt,
            system=system,
            resolved_model=resolved_model,
            timeout=timeout,
        )


async def chat_parallel(
    tasks: list[dict],
) -> list[str]:
    """
    Führt mehrere LLM-Anfragen parallel aus — nutzt alle VRAM-Kapazität.
    tasks: List von {"prompt": str, "system": str, "task_type": str, "model": str}
    Gibt Liste von Antworten zurück (gleiche Reihenfolge wie tasks).
    """
    async def _one(t: dict) -> str:
        return await chat(
            prompt=t.get("prompt", ""),
            system=t.get("system", ""),
            model=t.get("model"),
            task_type=t.get("task_type", "chat"),
            timeout=t.get("timeout", 120.0),
        )

    return list(await asyncio.gather(*[_one(t) for t in tasks]))


async def is_available() -> bool:
    """Prüft ob der aktive Provider erreichbar/konfiguriert ist."""
    if provider() == "github":
        return bool(GITHUB_MODELS_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return r.status_code == 200
    except Exception:
        return False


async def loaded_models() -> list[dict]:
    """Gibt aktuell relevante Modelle zurück."""
    if provider() == "github":
        names = [
            GITHUB_CHAT_MODEL,
            GITHUB_REASONING_MODEL,
            GITHUB_CODE_MODEL,
        ]
        return [{"name": name, "provider": "github"} for name in dict.fromkeys(names)]
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
        if r.status_code == 200:
            return r.json().get("models", [])
    except Exception:
        pass
    return []


async def available_models() -> list[str]:
    """Gibt alle verfügbaren Modell-Namen des aktiven Providers zurück."""
    if provider() == "github":
        return list(dict.fromkeys(GITHUB_MODEL_ROUTING.values()))
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []
