"""
tests/unit/agents/hermes/test_handle_smoke.py

Smoke-Tests für den Hermes-Reasoner-Agenten.
"""
from agents.hermes.agent import HermesReasonerAgent
from agents._base.agent import Task


class TestHermesSmoke:

    def test_chain_of_thought_erfolgreich(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="chain_of_thought", payload={"question": "Was ist 2+2?"})
        result = agent.run(task)
        assert result.success is True
        assert result.agent_id == "hermes-reasoner"

    def test_debate_task_erfolgreich(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="debate", payload={"topic": "KI vs. Mensch"})
        result = agent.run(task)
        assert result.success is True

    def test_hypothesis_task_erfolgreich(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="hypothesis", payload={"claim": "Redis ist schneller als Postgres für Caching"})
        result = agent.run(task)
        assert result.success is True

    def test_research_synthesis_erfolgreich(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="research_synthesis", payload={"sources": ["doc1", "doc2"]})
        result = agent.run(task)
        assert result.success is True

    def test_payload_enthaelt_reasoning_struktur(self):
        """Phase-2-Skelett enthält die richtigen Felder für spätere LLM-Befüllung."""
        agent = HermesReasonerAgent()
        task = Task(task_type="chain_of_thought", payload={})
        result = agent.run(task)
        assert "reasoning_steps" in result.payload
        assert "conclusion" in result.payload
        assert "sources" in result.payload

    def test_zone_public_erlaubt(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="debate", zone="PUBLIC", payload={})
        result = agent.run(task)
        assert result.success is True

    def test_zone_workspace_erlaubt(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="debate", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True
