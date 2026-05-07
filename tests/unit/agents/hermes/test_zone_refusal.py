"""
tests/unit/agents/hermes/test_zone_refusal.py

Zone-Refusal-Tests für den Hermes-Reasoner-Agenten.
"""
import pytest

from agents.hermes.agent import HermesReasonerAgent
from agents._base.agent import Task


class TestHermesZoneRefusal:

    def test_family_private_abgelehnt(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="chain_of_thought", zone="FAMILY_PRIVATE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_sacred_abgelehnt(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="debate", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_quarantine_abgelehnt(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="research_synthesis", zone="QUARANTINE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_error_message_enthaelt_zone(self):
        agent = HermesReasonerAgent()
        task = Task(task_type="chain_of_thought", zone="FAMILY_PRIVATE", payload={})
        result = agent.run(task)
        assert result.error is not None
        assert "FAMILY_PRIVATE" in result.error or "Zone" in result.error
