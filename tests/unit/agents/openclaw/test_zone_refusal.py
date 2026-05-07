"""
tests/unit/agents/openclaw/test_zone_refusal.py

Zone-Refusal-Tests für den OpenClaw-Agenten.
"""
import pytest

from agents.openclaw.agent import OpenClawAgent
from agents._base.agent import Task


class TestOpenClawZoneRefusal:

    def test_sacred_abgelehnt(self):
        agent = OpenClawAgent()
        task = Task(task_type="web_fetch", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_family_private_bei_externem_io_abgelehnt(self):
        """FAMILY_PRIVATE + externer I/O = REFUSE (Invariante aus MULTI-AGENT-ARCHITECTURE)."""
        agent = OpenClawAgent()
        task = Task(task_type="web_fetch", zone="FAMILY_PRIVATE", payload={})
        result = agent.run(task)
        assert result.success is False
        assert "REFUSE" in result.error or "Familie" in result.error or "FAMILY" in result.error

    def test_sacred_bei_api_call_abgelehnt(self):
        agent = OpenClawAgent()
        task = Task(task_type="api_call_external", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_family_private_bei_api_call_abgelehnt(self):
        agent = OpenClawAgent()
        task = Task(task_type="api_call_external", zone="FAMILY_PRIVATE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_unbekannte_zone_raises_bei_task(self):
        with pytest.raises(ValueError):
            Task(task_type="web_fetch", zone="UNKNOWN", payload={})
