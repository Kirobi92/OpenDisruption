"""
services/telegram/keycodi/llm.py
Lokale LLM-Anbindung via Ollama — RTX 3090 optimiert.

Strategie (24 GB VRAM, 24 CPU-Kerne, 32 GB RAM):
  - qwen2.5-coder:32b als primäres Code-Modell (passt vollständig in VRAM mit q4_K_M)
  - llama3.1:8b als schnelles Chat/Status-Modell (parallel geladen)
  - deepseek-r1:32b als Reasoning-Modell (on-demand, ersetzt Code-Modell im VRAM)
  - Bis zu 4 parallele Anfragen via OLLAMA_NUM_PARALLEL=4
  - MAX_LOADED_MODELS=2 → Code + Chat immer warm
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Optional

import httpx

from .config import (
    OLLAMA_BASE_URL,
    OLLAMA_DEFAULT_MODEL,
    OLLAMA_CODE_MODEL,
    MAX_PARALLEL_LOCAL_AGENTS,
)

log = logging.getLogger("keycodi.llm")

# Semaphore: max. 4 gleichzeitige LLM-Requests (entspricht OLLAMA_NUM_PARALLEL)
_sem = asyncio.Semaphore(MAX_PARALLEL_LOCAL_AGENTS)

# Modell-Routing: Aufgaben-Typ → bestes lokales Modell
MODEL_ROUTING: dict[str, str] = {
    "code":        OLLAMA_CODE_MODEL,         # qwen2.5-coder:32b
    "reasoning":   "deepseek-r1:32b",
    "chat":        OLLAMA_DEFAULT_MODEL,       # llama3.1:8b
    "status":      OLLAMA_DEFAULT_MODEL,
    "summary":     OLLAMA_DEFAULT_MODEL,
    "embedding":   "nomic-embed-text",
}


def model_for(task_type: str) -> str:
    return MODEL_ROUTING.get(task_type, OLLAMA_DEFAULT_MODEL)


async def chat(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    task_type: str = "chat",
    timeout: float = 120.0,
) -> str:
    """Einfacher Chat-Call — gibt die vollständige Antwort zurück."""
    resolved_model = model or model_for(task_type)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    async with _sem:
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
                            "num_thread": 6,   # CPU-Threads pro Request (6×4=24 bei 4 parallelen)
                            "num_gpu": 99,     # Alle GPU-Layer verwenden
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
    """Prüft ob Ollama erreichbar ist."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return r.status_code == 200
    except Exception:
        return False


async def loaded_models() -> list[dict]:
    """Gibt aktuell geladene Modelle zurück (Ollama /api/ps)."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/ps")
        if r.status_code == 200:
            return r.json().get("models", [])
    except Exception:
        pass
    return []


async def available_models() -> list[str]:
    """Gibt alle verfügbaren Modell-Namen zurück."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []
