"""
agents/hermes/agent.py — Hermes-Reasoner-Agent-Skelett

Zuständigkeit (aus AGENT-DECISION-MATRIX.md §B.2):
  - Multi-Step-Reasoning, Chain-of-Thought
  - Pro/Contra-Debatte
  - Hypothesen-Generierung + Validierung
  - Research-Synthese (Multi-Source)

Erlaubte Zonen: PUBLIC, WORKSPACE (Input & Output)

Hinweis: Dieser Agent heißt intern "hermes-reasoner" um Kollision mit
dem bestehenden "hermes-extractor" zu vermeiden (siehe MULTI-AGENT-ARCHITECTURE.md §3.1).

Zone: WORKSPACE
Autor: keycodi
Version: 1.0 (Phase 2)
"""

from __future__ import annotations

from agents._base.agent import BaseAgent, AgentResult, Task


class HermesReasonerAgent(BaseAgent):
    """
    Reasoning-Agent: Logik, Debatte, Hypothesen, Synthese.

    Headless-Aufruf:
        agent = HermesReasonerAgent()
        result = agent.run(Task(
            task_type="chain_of_thought",
            payload={"question": "Warum ist Rust schneller als Python?"}
        ))
    """

    agent_id = "hermes-reasoner"
    allowed_input_zones = frozenset({"PUBLIC", "WORKSPACE"})
    allowed_output_zones = frozenset({"PUBLIC", "WORKSPACE"})

    # Bekannte Task-Typen dieses Agenten
    KNOWN_TASK_TYPES = frozenset({
        "chain_of_thought",
        "debate",
        "hypothesis",
        "research_synthesis",
        "multi_step_reasoning",
    })

    def handle(self, task: Task) -> AgentResult:
        """
        Echo-Skelett: Gibt strukturiertes Reasoning-Gerüst zurück.
        Phase 4+ ersetzt diesen Body mit echtem LLM-Chain-of-Thought.
        """
        return AgentResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            zone=task.zone,
            success=True,
            payload={
                "echo": task.payload,
                "task_type": task.task_type,
                "reasoning_steps": [],   # Phase 4: befüllt mit CoT-Schritten
                "conclusion": None,       # Phase 4: abgeleitete Schlussfolgerung
                "confidence": None,       # Phase 4: berechneter Konfidenzwert
                "sources": [],            # Phase 4: referenzierte ContextDB-Keys
                "status": "skeleton_ok",
                "note": "Phase-2-Skelett — noch kein LLM-Reasoning",
            },
            confidence=1.0,
        )
