"""
tests/unit/agents/obsidian/test_zone_refusal.py

Zone-Refusal-Tests für den Obsidian-Agenten.
"""
import pytest

from agents.obsidian.agent import ObsidianAgent
from agents._base.agent import Task


class TestObsidianZoneRefusal:

    def test_sacred_zone_abgelehnt(self):
        agent = ObsidianAgent()
        task = Task(task_type="vault_read", zone="SACRED", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_quarantine_zone_abgelehnt(self):
        agent = ObsidianAgent()
        task = Task(task_type="vault_read", zone="QUARANTINE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_family_private_zone_read_erlaubt(self, tmp_path):
        """Obsidian ist der EINZIGE neue Agent der FAMILY_PRIVATE anfassen darf."""
        note = tmp_path / "family" / "note.md"
        note.parent.mkdir(parents=True)
        note.write_text("privat", encoding="utf-8")
        agent = ObsidianAgent(vault_path=tmp_path)
        task = Task(task_type="vault_read", zone="FAMILY_PRIVATE", payload={"path": "family/note.md"})
        result = agent.run(task)
        assert result.success is True

    def test_sacred_pfad_in_workspace_zone_abgelehnt(self):
        """Pfad-Prüfung ist unabhängig von der Zone."""
        agent = ObsidianAgent()
        task = Task(
            task_type="vault_read",
            zone="WORKSPACE",
            payload={"path": "sacred/something.md"},
        )
        result = agent.run(task)
        assert result.success is False
