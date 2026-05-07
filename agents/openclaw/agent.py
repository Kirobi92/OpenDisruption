"""
agents/openclaw/agent.py — OpenClaw-Agent-Skelett

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Web-Fetch / Scraping (PUBLIC URLs)
  - Externe API-Calls (ohne private Daten)
  - Lokale Filesystem-Operationen in PUBLIC/WORKSPACE
  - Browser-Automation (requires_approval=True wenn schreibend)

Erlaubte Zonen:
  Input:  PUBLIC, WORKSPACE, QUARANTINE
  Output: PUBLIC, WORKSPACE, QUARANTINE

Sicherheits-Invariante: Externe Calls mit privaten Daten → sofort REFUSE.

Zone: WORKSPACE
Autor: keycodi
Version: 1.0 (Phase 2)
"""

from __future__ import annotations

from agents._base.agent import BaseAgent, AgentResult, Task


class OpenClawAgent(BaseAgent):
    """
    Tool-Use-Agent: Web-Fetch, API-Calls, Filesystem, Browser-Automation.

    Headless-Aufruf:
        agent = OpenClawAgent()
        result = agent.run(Task(task_type="web_fetch", payload={"url": "https://..."}))
    """

    agent_id = "openclaw"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE", "QUARANTINE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE", "QUARANTINE"})

    # Task-Typen mit externem I/O die NIEMALS private Daten tragen dürfen
    EXTERNAL_IO_TYPES = frozenset({
        "web_fetch",
        "api_call_external",
        "browser_automation",
    })

    # Task-Typen die Approval erfordern wenn schreibend
    APPROVAL_REQUIRED_TYPES = frozenset({
        "browser_automation_write",
        "filesystem_write_quarantine",
    })

    def handle(self, task: Task) -> AgentResult:
        """
        Echo-Skelett: Prüft keine privaten Daten in externen Calls.
        Phase 4+ ersetzt diesen Body mit echtem Tool-Use.
        """
        # Sicherheits-Invariante: Keine FAMILY_PRIVATE/SACRED Daten nach außen
        if task.task_type in self.EXTERNAL_IO_TYPES:
            zone = task.zone
            if zone in {"FAMILY_PRIVATE", "SACRED"}:
                return AgentResult(
                    task_id=task.task_id,
                    agent_id=self.agent_id,
                    zone=zone,
                    success=False,
                    error=(
                        f"REFUSE: Externer I/O-Task '{task.task_type}' ist mit"
                        f" Zone '{zone}' nicht erlaubt."
                        " Private Daten verlassen den Host nicht."
                    ),
                    confidence=0.0,
                )

        # Approval-Check
        if task.task_type in self.APPROVAL_REQUIRED_TYPES and not task.approval_token:
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=f"Task-Typ '{task.task_type}' erfordert Human-Approval-Token.",
                confidence=0.0,
            )

        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "echo": task.payload,
                "task_type": task.task_type,
                "status": "skeleton_ok",
                "note": "Phase-2-Skelett — noch kein Tool-Use",
            },
            confidence=1.0,
        )
