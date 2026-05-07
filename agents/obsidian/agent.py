"""
agents/obsidian/agent.py — Obsidian-Vault-Agent-Skelett

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Vault-Read (Note-Abruf)
  - Vault-Write (neue Note / Update) — FAMILY_PRIVATE nur mit Approval
  - Knowledge-Graph-Query
  - Daily-Note-Generierung
  - MOC (Map of Content) Generierung

Erlaubte Zonen:
  Input:  PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal-only)
  Output: PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal-only)

Invariante: FAMILY_PRIVATE nur bei KIROBI_EGRESS_ALLOWED=false (lokal).
            Sacred-Pfade sind immer abgelehnt.

Zone: WORKSPACE
Autor: keycodi
Version: 1.0 (Phase 2)
"""

from __future__ import annotations

import os
from pathlib import Path

from agents._base.agent import BaseAgent, AgentResult, Task

# Default-Vault-Pfad: obsidian/ im Repo (Dev-Default laut ROADMAP.md Phase 3)
DEFAULT_VAULT_PATH = Path("obsidian")

# Sacred-Pfade sind immer verboten
_SACRED_PATHS = frozenset({"sacred", "sacred/", "sacred\\"})


def _is_sacred_path(path_str: str) -> bool:
    """Prüft ob ein Pfad in den sacred/-Bereich zeigt."""
    p = Path(path_str)
    parts = {str(part).lower() for part in p.parts}
    return bool(parts & _SACRED_PATHS) or path_str.lower().startswith("sacred")


class ObsidianAgent(BaseAgent):
    """
    Vault-Agent: Liest und schreibt den Obsidian-Vault, generiert MOCs und Daily Notes.

    Headless-Aufruf:
        agent = ObsidianAgent()
        result = agent.run(Task(
            task_type="vault_read",
            payload={"path": "obsidian/agents/opencode/00-Index.md"}
        ))
    """

    agent_id = "obsidian"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE"})

    APPROVAL_REQUIRED_ZONES = frozenset({"FAMILY_PRIVATE"})
    APPROVAL_REQUIRED_TYPES = frozenset({"vault_write"})

    def __init__(
        self,
        context_db=None,
        event_log_path: str = "kirobi-core/core-events.log",
        vault_path: Path | str | None = None,
    ) -> None:
        super().__init__(context_db=context_db, event_log_path=event_log_path)
        self._vault_path = Path(
            vault_path
            or os.environ.get("KIROBI_VAULT_PATH", str(DEFAULT_VAULT_PATH))
        )

    def handle(self, task: Task) -> AgentResult:
        """
        Vault-Operationen mit Zone- und Pfad-Validierung.
        Phase 3 ersetzt diesen Body mit echtem CRUD auf obsidian/.
        """
        payload = task.payload

        # Sacred-Pfad-Check
        target_path = str(payload.get("path", ""))
        if target_path and _is_sacred_path(target_path):
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=(
                    f"REFUSE: Vault-Zugriff auf Sacred-Pfad '{target_path}'"
                    " ist nicht erlaubt."
                ),
                confidence=0.0,
            )

        # FAMILY_PRIVATE schreibend → Approval erforderlich
        if (
            task.task_type in self.APPROVAL_REQUIRED_TYPES
            and task.zone in self.APPROVAL_REQUIRED_ZONES
            and not task.approval_token
        ):
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=(
                    f"Vault-Write in Zone '{task.zone}' erfordert Human-Approval-Token."
                ),
                confidence=0.0,
            )

        # Echo-Skelett — Phase 3 ersetzt mit echtem CRUD
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "echo": payload,
                "task_type": task.task_type,
                "vault_path": str(self._vault_path),
                "status": "skeleton_ok",
                "note": "Phase-2-Skelett — noch kein Vault-CRUD",
            },
            confidence=1.0,
        )
