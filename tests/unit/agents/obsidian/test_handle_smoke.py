"""
tests/unit/agents/obsidian/test_handle_smoke.py

Phase-3-Tests für den Obsidian-Vault-Agenten (echtes CRUD).
Alle File-I/O in temporäre Verzeichnisse — kein Zugriff auf echten Vault.
"""
from pathlib import Path

import pytest

from agents.obsidian.agent import ObsidianAgent, ZONE_TO_COLLECTION
from agents._base.agent import Task


# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture()
def vault(tmp_path):
    """Minimaler Testvault mit einer README."""
    (tmp_path / "agents" / "opencode").mkdir(parents=True)
    (tmp_path / "agents" / "hermes").mkdir(parents=True)
    (tmp_path / "shared-opendisruption" / "99-Inbox").mkdir(parents=True)
    readme = tmp_path / "README.md"
    readme.write_text("# Test Vault\n\n[[SomeLink]]\n", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def agent(vault):
    return ObsidianAgent(vault_path=vault)


# ─── vault_read ─────────────────────────────────────────────────────────────

class TestVaultRead:

    def test_read_existierende_note(self, agent, vault):
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={"path": "README.md"})
        result = agent.run(task)
        assert result.success is True
        assert "# Test Vault" in result.payload["content"]

    def test_read_absoluter_pfad(self, agent, vault):
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={"path": str(vault / "README.md")})
        result = agent.run(task)
        assert result.success is True

    def test_read_nicht_existierende_note(self, agent):
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={"path": "nope.md"})
        result = agent.run(task)
        assert result.success is False

    def test_read_liefert_backlinks(self, agent):
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={"path": "README.md"})
        result = agent.run(task)
        assert "SomeLink" in result.payload["backlinks"]

    def test_read_ohne_pfad(self, agent):
        task = Task(task_type="vault_read", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is False


# ─── vault_write ────────────────────────────────────────────────────────────

class TestVaultWrite:

    def test_write_neue_note(self, agent, vault):
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={"path": "agents/opencode/note.md", "content": "# Hello"},
        )
        result = agent.run(task)
        assert result.success is True
        assert result.payload["created"] is True
        assert (vault / "agents" / "opencode" / "note.md").read_text() == "# Hello"

    def test_write_erstellt_verzeichnis(self, agent, vault):
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={"path": "newdir/subdir/file.md", "content": "x"},
        )
        result = agent.run(task)
        assert result.success is True
        assert (vault / "newdir" / "subdir" / "file.md").exists()

    def test_write_mit_frontmatter(self, agent, vault):
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={
                "path": "agents/hermes/note.md",
                "content": "## Body",
                "prepend_frontmatter": True,
                "frontmatter_extra": {"tags": ["test"]},
            },
        )
        result = agent.run(task)
        assert result.success is True
        content = (vault / "agents" / "hermes" / "note.md").read_text()
        assert content.startswith("---")
        assert "zone: WORKSPACE" in content

    def test_write_update_existierende_note(self, agent, vault):
        note = vault / "README.md"
        old_content = note.read_text()
        task = Task(
            task_type="vault_write",
            zone="WORKSPACE",
            payload={"path": "README.md", "content": "# Updated"},
        )
        result = agent.run(task)
        assert result.success is True
        assert result.payload["created"] is False
        assert note.read_text() == "# Updated"

    def test_write_ohne_pfad(self, agent):
        task = Task(task_type="vault_write", zone="WORKSPACE", payload={"content": "x"})
        result = agent.run(task)
        assert result.success is False


# ─── vault_delete ────────────────────────────────────────────────────────────

class TestVaultDelete:

    def test_delete_existierende_note(self, agent, vault):
        note = vault / "README.md"
        task = Task(task_type="vault_delete", zone="WORKSPACE", payload={"path": "README.md"}, approval_token="tok")
        result = agent.run(task)
        assert result.success is True
        assert not note.exists()

    def test_delete_nicht_existierend(self, agent):
        task = Task(task_type="vault_delete", zone="WORKSPACE", payload={"path": "ghost.md"}, approval_token="tok")
        result = agent.run(task)
        assert result.success is False

    def test_delete_ohne_pfad(self, agent):
        task = Task(task_type="vault_delete", zone="WORKSPACE", payload={}, approval_token="tok")
        result = agent.run(task)
        assert result.success is False


# ─── vault_list ─────────────────────────────────────────────────────────────

class TestVaultList:

    def test_list_gesamter_vault(self, agent, vault):
        task = Task(task_type="vault_list", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True
        assert any("README.md" in f for f in result.payload["files"])

    def test_list_unterverzeichnis(self, agent, vault):
        (vault / "agents" / "opencode" / "note.md").write_text("x")
        task = Task(task_type="vault_list", zone="WORKSPACE", payload={"path": "agents/opencode"})
        result = agent.run(task)
        assert result.success is True
        assert result.payload["count"] >= 1

    def test_list_nicht_existierendes_verzeichnis(self, agent):
        task = Task(task_type="vault_list", zone="WORKSPACE", payload={"path": "nonexistent"})
        result = agent.run(task)
        assert result.success is False


# ─── vault_query_links ──────────────────────────────────────────────────────

class TestVaultQueryLinks:

    def test_outgoing_links_aus_readme(self, agent):
        task = Task(task_type="vault_query_links", zone="WORKSPACE", payload={"path": "README.md"})
        result = agent.run(task)
        assert result.success is True
        assert "SomeLink" in result.payload["outgoing_links"]

    def test_eingehende_links(self, agent, vault):
        # Note B verlinkt auf README
        (vault / "agents" / "opencode" / "note.md").write_text("[[README]] test", encoding="utf-8")
        task = Task(task_type="vault_query_links", zone="WORKSPACE", payload={"path": "README.md"})
        result = agent.run(task)
        assert result.success is True
        assert any("note.md" in l for l in result.payload["incoming_links"])


# ─── daily_note ─────────────────────────────────────────────────────────────

class TestDailyNote:

    def test_daily_note_wird_angelegt(self, agent, vault):
        task = Task(task_type="daily_note", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True
        assert result.payload["created"] is True
        note_path = vault / result.payload["path"]
        assert note_path.exists()

    def test_daily_note_idempotent(self, agent):
        task = Task(task_type="daily_note", zone="WORKSPACE", payload={})
        r1 = agent.run(task)
        r2 = agent.run(task)
        assert r1.success is True
        assert r2.success is True
        assert r2.payload["created"] is False


# ─── moc ────────────────────────────────────────────────────────────────────

class TestMoc:

    def test_moc_generiert_00_index(self, agent, vault):
        (vault / "agents" / "opencode" / "note.md").write_text("# Note", encoding="utf-8")
        task = Task(task_type="moc", zone="WORKSPACE", payload={"agent": "opencode"})
        result = agent.run(task)
        assert result.success is True
        moc = vault / "agents" / "opencode" / "00-Index.md"
        assert moc.exists()
        assert "note" in moc.read_text().lower()

    def test_moc_ohne_agent_payload(self, agent):
        task = Task(task_type="moc", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is False

    def test_moc_legt_verzeichnis_an(self, agent, vault):
        task = Task(task_type="moc", zone="WORKSPACE", payload={"agent": "newagent"})
        result = agent.run(task)
        assert result.success is True
        assert (vault / "agents" / "newagent" / "00-Index.md").exists()


# ─── zone_collection_map ────────────────────────────────────────────────────

class TestZoneCollectionMap:

    def test_alle_zonen_zurueckgegeben(self, agent):
        task = Task(task_type="zone_collection_map", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True
        mapping = result.payload["zone_collection_map"]
        assert "PUBLIC" in mapping
        assert "WORKSPACE" in mapping
        assert "FAMILY_PRIVATE" in mapping

    def test_zone_filter_workspace(self, agent):
        task = Task(task_type="zone_collection_map", zone="WORKSPACE", payload={"zone": "WORKSPACE"})
        result = agent.run(task)
        assert result.success is True
        assert result.payload["zone_collection_map"]["WORKSPACE"]["collection"] == "kirobi_workspace"

    def test_unbekannte_zone(self, agent):
        task = Task(task_type="zone_collection_map", zone="WORKSPACE", payload={"zone": "UNKNOWN_ZONE"})
        result = agent.run(task)
        assert result.success is False

    def test_embedding_mismatch_public_hat_768dim(self, agent):
        """PUBLIC muss nomic-embed-text (768d) sein — kein bge-m3-Mismatch."""
        task = Task(task_type="zone_collection_map", zone="WORKSPACE", payload={"zone": "PUBLIC"})
        result = agent.run(task)
        assert result.payload["zone_collection_map"]["PUBLIC"]["dim"] == 768
        assert result.payload["zone_collection_map"]["PUBLIC"]["model"] == "nomic-embed-text"

    def test_embedding_mismatch_workspace_hat_1024dim(self, agent):
        """WORKSPACE muss bge-m3 (1024d) sein."""
        task = Task(task_type="zone_collection_map", zone="WORKSPACE", payload={"zone": "WORKSPACE"})
        result = agent.run(task)
        assert result.payload["zone_collection_map"]["WORKSPACE"]["dim"] == 1024
        assert result.payload["zone_collection_map"]["WORKSPACE"]["model"] == "bge-m3"


# ─── Sacred-Pfad-Reject ─────────────────────────────────────────────────────

class TestSacredPathRefusal:

    @pytest.mark.parametrize("path", [
        "sacred/family-secrets.md",
        "sacred/private.md",
        "sacred",
        "Sacred/file.md",
    ])
    def test_sacred_pfad_immer_abgelehnt(self, agent, path):
        for task_type in ("vault_read", "vault_write", "vault_delete"):
            task = Task(
                task_type=task_type,
                zone="WORKSPACE",
                payload={"path": path, "content": "x"},
                approval_token="even-with-token",
            )
            result = agent.run(task)
            assert result.success is False, f"{task_type} mit Pfad '{path}' sollte REFUSE sein"


# ─── FAMILY_PRIVATE Approval ────────────────────────────────────────────────

class TestFamilyPrivateApproval:

    def test_write_ohne_token_abgelehnt(self, agent, vault):
        task = Task(
            task_type="vault_write",
            zone="FAMILY_PRIVATE",
            payload={"path": "family/note.md", "content": "x"},
        )
        result = agent.run(task)
        assert result.success is False
        assert "Approval" in result.error or "approval" in result.error.lower()

    def test_write_mit_token_erlaubt(self, agent, vault):
        task = Task(
            task_type="vault_write",
            zone="FAMILY_PRIVATE",
            payload={"path": "family/note.md", "content": "x"},
            approval_token="sven-ok",
        )
        result = agent.run(task)
        assert result.success is True

    def test_read_ohne_token_erlaubt(self, agent, vault):
        """Lesen von FAMILY_PRIVATE braucht kein Token."""
        note = vault / "family" / "note.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("privat", encoding="utf-8")
        task = Task(
            task_type="vault_read",
            zone="FAMILY_PRIVATE",
            payload={"path": "family/note.md"},
        )
        result = agent.run(task)
        assert result.success is True


# ─── Unbekannter Task-Typ ────────────────────────────────────────────────────

class TestUnknownTaskType:

    def test_unbekannter_typ_gibt_noop_zurueck(self, agent):
        task = Task(task_type="gibberish_op", zone="WORKSPACE", payload={})
        result = agent.run(task)
        assert result.success is True
        assert result.payload["status"] == "unknown_task_type_noop"
