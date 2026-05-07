"""
tests/unit/agents/openclaw/test_handle_smoke.py

Smoke-Tests für den OpenClaw-Agenten.
"""
from agents.openclaw.agent import OpenClawAgent
from agents._base.agent import Task


class TestOpenClawSmoke:

    def test_web_fetch_public_erfolgreich(self):
        agent = OpenClawAgent()
        task = Task(task_type="web_fetch", zone="PUBLIC", payload={"url": "https://example.com"})
        result = agent.run(task)
        assert result.success is True
        assert result.agent_id == "openclaw"

    def test_api_call_workspace_erfolgreich(self):
        agent = OpenClawAgent()
        task = Task(task_type="api_call_external", zone="WORKSPACE", payload={"endpoint": "/api/v1"})
        result = agent.run(task)
        assert result.success is True

    def test_filesystem_op_workspace_erfolgreich(self):
        agent = OpenClawAgent()
        task = Task(task_type="filesystem_read", zone="WORKSPACE", payload={"path": "docs/"})
        result = agent.run(task)
        assert result.success is True

    def test_quarantine_input_erlaubt(self):
        """OpenClaw darf QUARANTINE-Zonen verarbeiten (z.B. Web-Scrape-Ergebnisse)."""
        agent = OpenClawAgent()
        task = Task(task_type="filesystem_read", zone="QUARANTINE", payload={})
        result = agent.run(task)
        assert result.success is True

    def test_result_enthaelt_task_type(self):
        agent = OpenClawAgent()
        task = Task(task_type="web_fetch", zone="PUBLIC", payload={})
        result = agent.run(task)
        assert result.payload["task_type"] == "web_fetch"


class TestOpenClawApprovalPflicht:

    def test_browser_automation_write_ohne_token_abgelehnt(self):
        agent = OpenClawAgent()
        task = Task(task_type="browser_automation_write", payload={})
        result = agent.run(task)
        assert result.success is False
        assert "Approval" in result.error

    def test_browser_automation_write_mit_token_erlaubt(self):
        agent = OpenClawAgent()
        task = Task(
            task_type="browser_automation_write",
            payload={},
            approval_token="sven-ok",
        )
        result = agent.run(task)
        assert result.success is True
