"""
services/telegram/keycodi/parallel.py
Multi-Agenten Parallel-Execution Engine — RTX 3090 / 24 CPU-Kerne optimiert.

Architektur:
  - Jeder Sub-Task läuft als asyncio.Task
  - LLM-Semaphore in llm.py begrenzt auf 4 parallele GPU-Requests
  - CPU-bound Tasks (Vault-CRUD, DB) laufen direkt in asyncio-Loop
  - Cloud-Modelle: max. 3 parallele externe API-Calls
  - Ergebnis-Aggregation mit Timeout-Handling
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

from .config import MAX_PARALLEL_LOCAL_AGENTS, MAX_PARALLEL_CLOUD_MODELS

log = logging.getLogger("keycodi.parallel")

# Semaphore für Cloud-API-Calls (max. 3 parallel laut Policy)
_cloud_sem = asyncio.Semaphore(MAX_PARALLEL_CLOUD_MODELS)


@dataclass
class SubTask:
    name: str
    coro: Coroutine
    timeout: float = 120.0
    is_cloud: bool = False
    sofort: bool = False


@dataclass
class SubTaskResult:
    name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration_s: float = 0.0


async def run_subtask(sub: SubTask) -> SubTaskResult:
    """Führt einen einzelnen SubTask aus — mit optionalem Cloud-Semaphore."""
    start = time.monotonic()
    try:
        if sub.is_cloud:
            async with _cloud_sem:
                result = await asyncio.wait_for(sub.coro, timeout=sub.timeout)
        else:
            result = await asyncio.wait_for(sub.coro, timeout=sub.timeout)
        return SubTaskResult(
            name=sub.name,
            success=True,
            result=result,
            duration_s=time.monotonic() - start,
        )
    except asyncio.TimeoutError:
        log.warning("SubTask '%s' timed out nach %.0fs", sub.name, sub.timeout)
        return SubTaskResult(
            name=sub.name,
            success=False,
            error=f"Timeout nach {sub.timeout:.0f}s",
            duration_s=time.monotonic() - start,
        )
    except Exception as exc:
        log.error("SubTask '%s' Fehler: %s", sub.name, exc)
        return SubTaskResult(
            name=sub.name,
            success=False,
            error=str(exc),
            duration_s=time.monotonic() - start,
        )


async def run_parallel(
    subtasks: list[SubTask],
    *,
    return_partial: bool = True,
) -> list[SubTaskResult]:
    """
    Führt alle SubTasks parallel aus.
    SOFORT-Tasks werden priorisiert (zuerst gestartet).
    return_partial=True: gibt auch bei Teilfehlern alle Ergebnisse zurück.
    """
    sofort = [s for s in subtasks if s.sofort]
    normal = [s for s in subtasks if not s.sofort]
    ordered = sofort + normal

    log.info(
        "Starte %d SubTasks parallel (%d SOFORT, %d normal)",
        len(ordered), len(sofort), len(normal),
    )

    results = await asyncio.gather(
        *[run_subtask(s) for s in ordered],
        return_exceptions=not return_partial,
    )
    return list(results)


def format_results_summary(results: list[SubTaskResult]) -> str:
    """Formatiert Ergebnisse als kompakte Textzeilen."""
    lines = []
    for r in results:
        icon = "✅" if r.success else "❌"
        dur = f"{r.duration_s:.1f}s"
        if r.success:
            lines.append(f"{icon} <b>{r.name}</b> ({dur})")
        else:
            lines.append(f"{icon} <b>{r.name}</b> ({dur}) — {r.error}")
    return "\n".join(lines)
