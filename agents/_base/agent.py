"""
agents/_base/agent.py — Basisklasse für alle KIDI/KEYBRODI-Agenten

Zone: WORKSPACE
Autor: keycodi
Version: 1.0 (Phase 2)
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Optionaler Import — kein harter Fehler wenn kidi noch nicht initialisiert ist
try:
    from kidi.context_db.client import ContextDB
    from kidi.context_db.errors import ContextDBError
    _CONTEXT_DB_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CONTEXT_DB_AVAILABLE = False
    ContextDB = None  # type: ignore[assignment,misc]
    ContextDBError = Exception  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Erlaubte Zonen-Werte (normalisiert)
VALID_ZONES = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"})


@dataclass
class Task:
    """Eingehende Aufgabe für einen Agenten."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    zone: str = "WORKSPACE"
    payload: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    approval_token: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if self.zone not in VALID_ZONES:
            raise ValueError(f"Ungültige Zone: {self.zone!r}. Erlaubt: {VALID_ZONES}")


@dataclass
class AgentResult:
    """Ergebnis einer Agent-Ausführung."""
    task_id: str
    agent_id: str
    zone: str
    success: bool
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    confidence: float = 1.0
    context_key: str | None = None  # Redis-Key falls in ContextDB geschrieben
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ZoneViolationError(Exception):
    """Aufgerufen wenn ein Agent versucht eine nicht erlaubte Zone zu lesen/schreiben."""


class BaseAgent(ABC):
    """
    Basisklasse für alle KIDI-Agenten.

    Subklassen müssen implementieren:
    - ``agent_id``: Eindeutiger Bezeichner (z.B. "opencode")
    - ``allowed_input_zones``: Welche Zonen darf der Agent als Input verarbeiten
    - ``allowed_output_zones``: Welche Zonen darf der Agent beschreiben
    - ``handle(task)``: Eigentliche Logik
    """

    # Zu überschreiben in Subklassen
    agent_id: str = "base"
    allowed_input_zones: frozenset[str] = frozenset({"PUBLIC", "WORKSPACE"})
    allowed_output_zones: frozenset[str] = frozenset({"PUBLIC", "WORKSPACE"})

    def __init__(
        self,
        context_db: "ContextDB | None" = None,
        event_log_path: str = "kirobi-core/core-events.log",
    ) -> None:
        self._context_db = context_db
        self._event_log_path = event_log_path

    # ─── Public API ───────────────────────────────────────────────────────────

    def run(self, task: Task) -> AgentResult:
        """
        Haupteinsprungpunkt. Validiert Zonen, delegiert an ``handle()``,
        schreibt Ergebnis in ContextDB und loggt den Event.
        """
        start = datetime.now(timezone.utc)

        # 1. Zonen-Validierung
        try:
            self._check_zone_input(task)
        except ZoneViolationError as exc:
            result = AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=str(exc),
                confidence=0.0,
            )
            self._log_event(
                level="WARN",
                action="zone_refusal",
                task_id=task.task_id,
                zone=task.zone,
                reason=str(exc),
            )
            return result

        # 2. Approval-Check
        if task.requires_approval and not task.approval_token:
            result = AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error="Aufgabe erfordert Human-Approval-Token",
                confidence=0.0,
            )
            self._log_event(
                level="WARN",
                action="approval_required",
                task_id=task.task_id,
                zone=task.zone,
            )
            return result

        # 3. Eigentliche Ausführung
        try:
            result = self.handle(task)
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = int(
                (datetime.now(timezone.utc) - start).total_seconds() * 1000
            )
            result = AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                confidence=0.0,
            )
            self._log_event(
                level="ERROR",
                action="handle_exception",
                task_id=task.task_id,
                zone=task.zone,
                reason=result.error,
                latency_ms=elapsed_ms,
            )
            return result

        # 4. Ergebnis in ContextDB schreiben (optional)
        if self._context_db is not None and result.success:
            try:
                ctx_key = self._write_context(task, result)
                result.context_key = ctx_key
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "ContextDB-Schreibfehler für Task %s: %s", task.task_id, exc
                )

        # 5. Audit-Log
        elapsed_ms = int(
            (datetime.now(timezone.utc) - start).total_seconds() * 1000
        )
        self._log_event(
            level="INFO",
            action="handle_complete",
            task_id=task.task_id,
            zone=task.zone,
            success=str(result.success).lower(),
            latency_ms=elapsed_ms,
        )
        return result

    # ─── Zu implementieren ────────────────────────────────────────────────────

    @abstractmethod
    def handle(self, task: Task) -> AgentResult:
        """Eigentliche Agent-Logik. Wird von ``run()`` aufgerufen."""

    # ─── Interne Hilfsmethoden ────────────────────────────────────────────────

    def _check_zone_input(self, task: Task) -> None:
        """Wirft ZoneViolationError wenn die Task-Zone nicht erlaubt ist."""
        if task.zone not in self.allowed_input_zones:
            raise ZoneViolationError(
                f"Agent '{self.agent_id}' darf Zone '{task.zone}' nicht als Input"
                f" verarbeiten. Erlaubt: {sorted(self.allowed_input_zones)}"
            )

    def _write_context(self, task: Task, result: AgentResult) -> str:
        """Schreibt das Ergebnis in ContextDB und gibt den Key zurück."""
        if self._context_db is None:  # pragma: no cover
            raise RuntimeError("ContextDB nicht konfiguriert")

        entry_id = str(uuid.uuid4())
        from kidi.context_db.keys import make_key  # noqa: PLC0415

        key = make_key(
            zone=task.zone,
            agent=self.agent_id,
            category="result",
            uid=entry_id,
        )
        self._context_db.put(
            key=key,
            payload={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "result": result.payload,
                "confidence": result.confidence,
                "error": result.error,
            },
            zone=task.zone,
        )
        return key

    def _log_event(self, level: str, action: str, **kwargs: Any) -> None:
        """Schreibt einen strukturierten Event-Log-Eintrag (kirobi-core-Konvention)."""
        parts = [f"[{datetime.now(timezone.utc).isoformat()}]"]
        parts.append(f"[{self.agent_id}]")
        parts.append(level)
        parts.append(f"action={action}")
        for k, v in kwargs.items():
            val = str(v).replace('"', "'")
            parts.append(f'{k}="{val}"' if " " in str(v) else f"{k}={v}")
        line = " ".join(parts)
        logger.info(line)
        try:
            with open(self._event_log_path, "a", encoding="utf-8") as fh:
                fh.write(f" {line}\n")
        except OSError:
            pass  # Log-Fehler darf Agent nicht crashen
