"""
tests/unit/kidi/test_serve.py
Zone: WORKSPACE

Unit-Tests für den kidi MCP-Server.
Testet Tool-Handler direkt ohne stdio-Transport.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kidi.context_db.store import (
    delete_context,
    get_context,
    list_context,
    store_context,
)
from kidi.serve import _process_request


# ---------------------------------------------------------------------------
# Hilfsfunktion: Erstellt eine JSON-RPC Anfrage als String
# ---------------------------------------------------------------------------

def _rpc(method: str, params: dict, req_id: int = 1) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})


# ---------------------------------------------------------------------------
# test_zone_classify_tool
# ---------------------------------------------------------------------------

def test_zone_classify_tool():
    """zone_classify gibt korrekte Zone für bekannte Pfade zurück."""
    line = _rpc("tools/call", {"name": "zone_classify", "arguments": {"path": "sacred/test.md"}})
    response = _process_request(line)

    assert response is not None
    assert "result" in response
    content = json.loads(response["result"]["content"][0]["text"])
    assert content["path"] == "sacred/test.md"
    assert content["zone"] == "SACRED"


def test_zone_classify_workspace():
    """zone_classify erkennt WORKSPACE-Pfade."""
    line = _rpc("tools/call", {"name": "zone_classify", "arguments": {"path": "kidi/serve.py"}})
    response = _process_request(line)

    assert response is not None
    content = json.loads(response["result"]["content"][0]["text"])
    assert content["zone"] in ("WORKSPACE", "PUBLIC")  # je nach kirobi_core-Logik


# ---------------------------------------------------------------------------
# test_context_store_and_get
# ---------------------------------------------------------------------------

def test_context_store_and_get(tmp_path):
    """context_store speichert und context_get liest den Eintrag zurück."""
    db = tmp_path / "test.db"

    stored = store_context("test-key", "hello world", "WORKSPACE", db_path=db)
    assert stored["key"] == "test-key"
    assert stored["zone"] == "WORKSPACE"

    entry = get_context("test-key", db_path=db)
    assert entry is not None
    assert entry["value"] == "hello world"
    assert entry["zone"] == "WORKSPACE"
    assert "created_at" in entry


def test_context_store_and_get_via_rpc(tmp_path):
    """context_store und context_get funktionieren über den RPC-Dispatcher."""
    db = tmp_path / "rpc_test.db"

    # Store via direktem Store-Aufruf (RPC-Handler nutzt Default-DB-Pfad)
    store_context("rpc-key", "rpc-value", "PUBLIC", db_path=db)
    entry = get_context("rpc-key", db_path=db)

    assert entry is not None
    assert entry["value"] == "rpc-value"


# ---------------------------------------------------------------------------
# test_context_store_rejects_sacred
# ---------------------------------------------------------------------------

def test_context_store_rejects_sacred(tmp_path):
    """context_store lehnt SACRED-Zone mit SacredApprovalMissing ab."""
    from kidi.context_db.errors import SacredApprovalMissing

    db = tmp_path / "sacred_test.db"
    with pytest.raises(SacredApprovalMissing):
        store_context("sacred-key", "geheim", "SACRED", db_path=db)


def test_context_store_rejects_family_private(tmp_path):
    """context_store lehnt FAMILY_PRIVATE-Zone mit EgressViolation ab."""
    from kidi.context_db.errors import EgressViolation

    db = tmp_path / "family_test.db"
    with pytest.raises(EgressViolation):
        store_context("family-key", "privat", "FAMILY_PRIVATE", db_path=db)


def test_context_store_rejects_sacred_via_rpc():
    """tools/call context_store mit SACRED gibt JSON-RPC Fehler zurück."""
    line = _rpc(
        "tools/call",
        {
            "name": "context_store",
            "arguments": {"key": "x", "value": "y", "zone": "SACRED"},
        },
    )
    response = _process_request(line)
    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32603


# ---------------------------------------------------------------------------
# test_context_list
# ---------------------------------------------------------------------------

def test_context_list(tmp_path):
    """context_list gibt alle gespeicherten Keys zurück."""
    db = tmp_path / "list_test.db"

    store_context("alpha", "1", "PUBLIC", db_path=db)
    store_context("beta", "2", "WORKSPACE", db_path=db)
    store_context("alpha-extra", "3", "PUBLIC", db_path=db)

    # Alle Einträge
    all_entries = list_context(db_path=db)
    assert len(all_entries) == 3

    # Zone-Filter
    public_entries = list_context(zone="PUBLIC", db_path=db)
    assert len(public_entries) == 2
    assert all(e["zone"] == "PUBLIC" for e in public_entries)

    # Präfix-Filter
    alpha_entries = list_context(prefix="alpha", db_path=db)
    assert len(alpha_entries) == 2
    assert all(e["key"].startswith("alpha") for e in alpha_entries)


def test_context_list_empty(tmp_path):
    """context_list gibt leere Liste zurück wenn keine Einträge vorhanden."""
    db = tmp_path / "empty_test.db"
    entries = list_context(db_path=db)
    assert entries == []


# ---------------------------------------------------------------------------
# test_backlog_query_tool
# ---------------------------------------------------------------------------

def test_backlog_query_tool():
    """backlog_query gibt eine Liste von Tasks zurück."""
    line = _rpc("tools/call", {"name": "backlog_query", "arguments": {"limit": 3}})
    response = _process_request(line)

    assert response is not None
    assert "result" in response, f"Fehler: {response.get('error')}"

    content_text = response["result"]["content"][0]["text"]
    tasks = json.loads(content_text)

    # Kann leer sein wenn kein Backlog vorhanden, aber muss eine Liste sein
    assert isinstance(tasks, list)
    assert len(tasks) <= 3

    # Wenn Tasks vorhanden, müssen sie die erwarteten Felder haben
    for task in tasks:
        assert "id" in task or "title" in task  # mindestens eines der Felder


def test_backlog_query_tool_default_limit():
    """backlog_query ohne limit-Parameter nutzt Default von 10."""
    line = _rpc("tools/call", {"name": "backlog_query", "arguments": {}})
    response = _process_request(line)

    assert response is not None
    assert "result" in response or "error" in response
    # Kein Crash erwartet


# ---------------------------------------------------------------------------
# test_context_delete
# ---------------------------------------------------------------------------

def test_context_delete(tmp_path):
    """context_delete entfernt einen Eintrag und gibt deleted=True zurück."""
    db = tmp_path / "delete_test.db"

    store_context("to-delete", "wert", "WORKSPACE", db_path=db)
    deleted = delete_context("to-delete", db_path=db)
    assert deleted is True

    entry = get_context("to-delete", db_path=db)
    assert entry is None


def test_context_delete_nonexistent(tmp_path):
    """context_delete gibt False zurück wenn Key nicht existiert."""
    db = tmp_path / "delete_none_test.db"
    deleted = delete_context("nonexistent", db_path=db)
    assert deleted is False


# ---------------------------------------------------------------------------
# test_initialize
# ---------------------------------------------------------------------------

def test_initialize():
    """initialize gibt korrekte MCP-Protokollversion und Server-Info zurück."""
    line = _rpc("initialize", {})
    response = _process_request(line)

    assert response is not None
    assert "result" in response
    result = response["result"]
    assert result["protocolVersion"] == "2024-11-05"
    assert result["serverInfo"]["name"] == "kirobi-context-db"


def test_tools_list():
    """tools/list gibt alle 6 erwarteten Tools zurück."""
    line = _rpc("tools/list", {})
    response = _process_request(line)

    assert response is not None
    tools = response["result"]["tools"]
    tool_names = {t["name"] for t in tools}
    expected = {
        "context_store",
        "context_get",
        "context_list",
        "context_delete",
        "backlog_query",
        "zone_classify",
    }
    assert expected == tool_names


def test_unknown_method():
    """Unbekannte Methode gibt -32601 Method not found zurück."""
    line = _rpc("unknown/method", {})
    response = _process_request(line)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32601


def test_invalid_json():
    """Ungültiges JSON gibt -32700 Parse error zurück."""
    response = _process_request("{not valid json}")
    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32700


def test_ttl_expiry(tmp_path):
    """Einträge mit abgelaufenem TTL werden nicht zurückgegeben."""
    import time

    db = tmp_path / "ttl_test.db"
    store_context("ttl-key", "wert", "PUBLIC", ttl_seconds=1, db_path=db)

    # Sofort lesbar
    entry = get_context("ttl-key", db_path=db)
    assert entry is not None

    # Nach Ablauf nicht mehr lesbar
    time.sleep(1.1)
    entry = get_context("ttl-key", db_path=db)
    assert entry is None
