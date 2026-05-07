"""
agents/opencode/agent.py — OpenCode-Agent-Skelett

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Code generieren / refaktorieren
  - Code-Review, Lint, Test-Authoring
  - CI/CD-Änderungen (requires_approval=True)
  - Dependency-Updates (requires_approval=True)

Erlaubte Zonen: PUBLIC, WORKSPACE (Input & Output)

Zone: WORKSPACE
Autor: keycodi
Version: 1.0 (Phase 2)
"""

from __future__ import annotations

from agents._base.agent import BaseAgent, AgentResult, Task


class OpenCodeAgent(BaseAgent):
    """
    Coding-Agent: Code-Generierung, Refactoring, Reviews, Tests, CI/CD.

    Headless-Aufruf:
        agent = OpenCodeAgent()
        result = agent.run(Task(task_type="generate_code", payload={"prompt": "..."}))
    """

    agent_id = "opencode"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE"})

    # Task-Typen die Human-Approval erfordern (aus AGENT-DECISION-MATRIX.md)
    APPROVAL_REQUIRED_TYPES = frozenset({
        "ci_cd_change",
        "dependency_update",
        "commit",
        "push",
    })

    def handle(self, task: Task) -> AgentResult:
        """
        Echo-Skelett: Gibt die Task zurück, validiert Approval-Pflicht.
        Phase 4+ ersetzt diesen Body mit echtem LLM-Routing.
        """
        # Approval-Check für risikoreiche Task-Typen
        if task.task_type in self.APPROVAL_REQUIRED_TYPES and not task.approval_token:
            return AgentResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                zone=task.zone,
                success=False,
                error=(
                    f"Task-Typ '{task.task_type}' erfordert Human-Approval-Token."
                    " Setze task.approval_token oder task.requires_approval=False"
                    " nur wenn du weißt was du tust."
                ),
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
                "note": "Phase-2-Skelett — noch kein LLM-Routing",
            },
            confidence=1.0,
        )
