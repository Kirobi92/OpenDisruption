"""
tests/unit/agents/opencode/test_handle_smoke.py

Smoke-Tests für den OpenCode-Agenten.
Prüft: normaler Task läuft durch, Approval-Pflicht-Tasks werden korrekt behandelt.
"""
import pytest

from agents.opencode.agent import OpenCodeAgent
from agents._base.agent import Task


class TestOpenCodeSmoke:

    def test_einfacher_task_erfolgreich(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", payload={"prompt": "Hello World in Python"})
        result = agent.run(task)
        assert result.success is True
        assert result.agent_id == "opencode"
        assert result.zone == "WORKSPACE"
        assert result.error is None

    def test_result_enthaelt_echo(self):
        agent = OpenCodeAgent()
        task = Task(task_type="code_review", payload={"file": "main.py"})
        result = agent.run(task)
        assert result.success is True
        assert result.payload["echo"] == {"file": "main.py"}

    def test_task_id_wird_durchgereicht(self):
        agent = OpenCodeAgent()
        task = Task(task_id="test-uuid-123", task_type="generate_code", payload={})
        result = agent.run(task)
        assert result.task_id == "test-uuid-123"

    def test_zone_workspace_erlaubt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True

    def test_zone_public_erlaubt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", zone="PUBLIC", payload={})
        result = agent.run(task)
        assert result.success is True

    def test_confidence_ist_gesetzt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="generate_code", payload={})
        result = agent.run(task)
        assert 0.0 <= result.confidence <= 1.0


class TestOpenCodeApprovalPflicht:

    def test_ci_cd_change_ohne_token_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="ci_cd_change", payload={})
        result = agent.run(task)
        assert result.success is False
        assert "Approval" in result.error

    def test_dependency_update_ohne_token_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="dependency_update", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_commit_ohne_token_abgelehnt(self):
        agent = OpenCodeAgent()
        task = Task(task_type="commit", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_ci_cd_change_mit_token_erlaubt(self):
        agent = OpenCodeAgent()
        task = Task(
            task_type="ci_cd_change",
            payload={},
            approval_token="sven-approved-2026",
        )
        result = agent.run(task)
        assert result.success is True
