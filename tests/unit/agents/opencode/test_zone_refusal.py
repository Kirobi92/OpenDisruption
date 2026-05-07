"""
tests/unit/agents/opencode/test_zone_refusal.py

Zone-Refusal-Tests für den OpenCode-Agenten.
Prüft: Zonen außerhalb des erlaubten Bereichs werden abgelehnt.
"""
import pytest

from agents.opencode.agent import OpenCodeAgent
from agents._base.agent import Task


class TestOpenCodeZoneRefusal:

    def test_family_private_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="FAMILY_PRIVATE", payload={})
        result = agent.run(task)
        assert result.success is False
        assert "FAMILY_PRIVATE" in result.error or "Zone" in result.error

    def test_sacred_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_quarantine_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="QUARANTINE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_unbekannte_zone_raises_bei_task_erstellung(self):
        """Ungültige Zone wird bereits beim Task-Erstellen abgelehnt."""
        with pytest.raises(ValueError, match="Ungültige Zone"):
            Task(task_type="generate_code", zone="INVALID_ZONE", payload={})

    def test_zone_refusal_hat_keinen_context_key(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.context_key is None
