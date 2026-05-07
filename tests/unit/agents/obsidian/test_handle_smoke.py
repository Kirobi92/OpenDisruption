"""
tests/unit/agents/obsidian/test_handle_smoke.py

Smoke-Tests für den Obsidian-Vault-Agenten.
"""
from pathlib import Path

import pytest

from agents.obsidian.agent import ObsidianAgent
from agents._base.agent import Task


class TestObsidianSmoke:

    def test_vault_read_workspace_erfolgreich(self):
        agent = ObsidianAgent(vault_path=Path("obsidian"))
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={"path": "obsidian/README.md"})
        result = agent.run(task)
        assert result.success is True
        assert result.agent_id == "obsidian"

    def test_vault_write_workspace_ohne_token_erfolgreich(self):
        """WORKSPACE-Write braucht kein Approval."""
        agent = ObsidianAgent(vault_path=Path("obsidian"))
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={"path": "obsidian/test.md", "content": "# Test"},
        )
        result = agent.run(task)
        assert result.success is True

    def test_daily_note_task_erfolgreich(self):
        agent = ObsidianAgent()
        task = Task(task_type="daily_note", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True

    def test_moc_task_erfolgreich(self):
        agent = ObsidianAgent()
        task = Task(task_type="moc", zone="WORKSPACE", payload={"agent": "opencode"})
        result = agent.run(task)
        assert result.success is True

    def test_family_private_write_mit_token_erfolgreich(self):
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_write",
            zone="FAMILY_PRIVATE",
            payload={"path": "obsidian/family/note.md"},
            approval_token="sven-ok",
        )
        result = agent.run(task)
        assert result.success is True

    def test_family_private_read_ohne_token_erfolgreich(self):
        """Lesen von FAMILY_PRIVATE braucht kein Token (nur Schreiben)."""
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_read",
            zone="FAMILY_PRIVATE",
            payload={"path": "obsidian/family/note.md"},
        )
        result = agent.run(task)
        assert result.success is True

    def test_vault_path_wird_im_payload_zurueckgegeben(self):
        agent = ObsidianAgent(vault_path=Path("/tmp/test-vault"))
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert "vault_path" in result.payload


class TestObsidianSacredPathRefusal:

    def test_sacred_pfad_vault_read_abgelehnt(self):
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_read",
            zone="WORKSPACE",
            payload={"path": "sacred/family-secrets.md"},
        )
        result = agent.run(task)
        assert result.success is False
        assert "Sacred" in result.error or "REFUSE" in result.error

    def test_sacred_pfad_vault_write_abgelehnt(self):
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={"path": "sacred/private.md", "content": "..."},
            approval_token="even-with-token",
        )
        result = agent.run(task)
        assert result.success is False


class TestObsidianFamilyPrivateApproval:

    def test_family_private_write_ohne_token_abgelehnt(self):
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_write",
            zone="FAMILY_PRIVATE",
            payload={"path": "obsidian/family/note.md"},
        )
        result = agent.run(task)
        assert result.success is False
        assert "Approval" in result.error or "approval" in result.error.lower()
