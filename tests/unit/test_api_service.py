"""
Unit-Tests für services/api/main.py
Zone: WORKSPACE

asyncpg-Pool und httpx-Calls (Auth-Service, Ollama) werden vollständig gemockt.
Auth-Dependency wird durch einen Override ersetzt.
Kein laufender Service oder Datenbank erforderlich.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conversation_row(
    conv_id: str = "conv-1",
    user_id: str = "user-1",
    zone: str = "WORKSPACE",
) -> dict:
    """Erstellt eine Fake-DB-Zeile für conversations."""
    return {
        "id": conv_id,
        "user_id": user_id,
        "title": "Test Conversation",
        "zone": zone,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "archived": False,
    }


def _make_message_row(
    msg_id: str = "msg-1",
    conv_id: str = "conv-1",
    role: str = "assistant",
) -> dict:
    """Erstellt eine Fake-DB-Zeile für messages."""
    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "user_id": "user-1",
        "role": role,
        "content": "Test response",
        "model_used": "llama3.1:8b",
        "tokens_used": None,
        "attachments": "[]",
        "metadata": "{}",
        "created_at": datetime.now(timezone.utc),
    }


def _make_upload_row(file_id: str = "file-1", zone: str = "WORKSPACE") -> dict:
    return {
        "id": file_id,
        "filename": "test.txt",
        "file_path": "/data/uploads/testuser/workspace/test.txt",
        "file_size": 100,
        "mime_type": "text/plain",
        "zone": zone,
        "created_at": datetime.now(timezone.utc),
    }


class _AsyncContextManagerMock:
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=_AsyncContextManagerMock(mock_conn))
    mock_pool.close = AsyncMock(return_value=None)
    return mock_pool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    TestClient mit gemocktem asyncpg-Pool und Auth-Dependency-Override.
    """
    import services.api.main as api

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    # Auth-Dependency überschreiben
    fake_user = api.User(id="user-1", username="testuser", display_name="Test User", role="admin")

    async def _fake_auth():
        return fake_user

    api.app.dependency_overrides[api.get_current_user] = _fake_auth

    with patch("services.api.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        with TestClient(api.app, raise_server_exceptions=False) as c:
            api.db_pool = mock_pool
            yield c, mock_conn

    api.app.dependency_overrides.clear()
    api.db_pool = None


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health muss 'healthy' zurückgeben wenn DB erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api"


def test_health_returns_unhealthy_on_db_error(client):
    """GET /health muss 'unhealthy' zurückgeben wenn DB nicht erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unhealthy"


# ---------------------------------------------------------------------------
# GET /conversations
# ---------------------------------------------------------------------------

def test_list_conversations_returns_empty_list(client):
    """GET /conversations muss leere Liste zurückgeben wenn keine vorhanden."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/conversations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_conversations_returns_list(client):
    """GET /conversations muss Liste mit Conversations zurückgeben."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_conversation_row()])

    resp = c.get("/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "conv-1"
    assert data[0]["zone"] == "WORKSPACE"


# ---------------------------------------------------------------------------
# POST /conversations
# ---------------------------------------------------------------------------

def test_create_conversation_with_zone_permission(client):
    """POST /conversations muss 201 zurückgeben wenn Zone-Permission vorhanden."""
    c, mock_conn = client
    conv_row = _make_conversation_row()
    # fetchrow für zone_permissions (can_write=True) und dann für conversation
    mock_conn.fetchrow = AsyncMock(side_effect=[
        {"can_write": True},  # zone permission check
        conv_row,             # conversation row
    ])

    resp = c.post("/conversations", json={"title": "Test", "zone": "WORKSPACE"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["zone"] == "WORKSPACE"


def test_create_conversation_without_zone_permission_returns_403(client):
    """POST /conversations muss 403 zurückgeben wenn keine Zone-Permission."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value={"can_write": False})

    resp = c.post("/conversations", json={"title": "Test", "zone": "WORKSPACE"})
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /conversations/{id}
# ---------------------------------------------------------------------------

def test_get_conversation_not_found_returns_404(client):
    """GET /conversations/{id} muss 404 zurückgeben wenn nicht gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/conversations/nonexistent-id")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_get_conversation_found(client):
    """GET /conversations/{id} muss Conversation zurückgeben wenn gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_conversation_row(conv_id="conv-42"))

    resp = c.get("/conversations/conv-42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "conv-42"


# ---------------------------------------------------------------------------
# GET /conversations/{id}/messages
# ---------------------------------------------------------------------------

def test_list_messages_conversation_not_found(client):
    """GET /conversations/{id}/messages muss 404 zurückgeben wenn Conversation fehlt."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/conversations/nonexistent/messages")
    assert resp.status_code == 404


def test_list_messages_returns_empty(client):
    """GET /conversations/{id}/messages muss leere Liste zurückgeben."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_conversation_row())
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/conversations/conv-1/messages")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /conversations/{id}/messages
# ---------------------------------------------------------------------------

def test_create_message_conversation_not_found(client):
    """POST /conversations/{id}/messages muss 404 zurückgeben wenn Conversation fehlt."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.post("/conversations/nonexistent/messages", json={"content": "Hello"})
    assert resp.status_code == 404


def test_create_message_missing_content_returns_422(client):
    """POST /conversations/{id}/messages ohne content muss 422 zurückgeben."""
    c, _ = client
    resp = c.post("/conversations/conv-1/messages", json={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /chat compatibility endpoint
# ---------------------------------------------------------------------------

def test_chat_compat_accepts_desktop_message(client):
    """POST /chat muss den Desktop-Chat-Vertrag bedienen."""
    c, _ = client

    with patch("services.api.main.call_ollama", AsyncMock(return_value="Hallo Sven.")) as mock_call:
        resp = c.post("/chat", json={"message": "Hallo KeyCodi"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Hallo Sven."
    assert data["response"] == "Hallo Sven."
    assert data["content"] == "Hallo Sven."
    assert data["zone"] == "WORKSPACE"
    mock_call.assert_awaited_once()
    _, kwargs = mock_call.call_args
    assert "FAMILY_PRIVATE" in kwargs["system_prompt"]
    assert "SACRED" in kwargs["system_prompt"]


def test_chat_compat_accepts_voice_messages_history(client):
    """POST /chat muss die letzte User-Nachricht aus Voice-History nutzen."""
    c, _ = client

    with patch("services.api.main.call_ollama", AsyncMock(return_value="Ich höre dich.")) as mock_call:
        resp = c.post(
            "/chat",
            json={
                "messages": [
                    {"role": "assistant", "content": "Hallo"},
                    {"role": "user", "content": "Kannst du mich hören?"},
                ]
            },
        )

    assert resp.status_code == 200
    assert resp.json()["response"] == "Ich höre dich."
    args, _ = mock_call.call_args
    assert args[0] == "Kannst du mich hören?"


def test_chat_compat_rejects_empty_payload(client):
    """POST /chat ohne User-Inhalt bleibt ein Validierungsfehler."""
    c, _ = client
    resp = c.post("/chat", json={"messages": [{"role": "assistant", "content": "Hallo"}]})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /uploads
# ---------------------------------------------------------------------------

def test_list_uploads_returns_empty(client):
    """GET /uploads muss leere Liste zurückgeben wenn keine Uploads vorhanden."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/uploads")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_uploads_with_zone_filter(client):
    """GET /uploads?zone=WORKSPACE muss nach Zone filtern."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_upload_row()])

    resp = c.get("/uploads?zone=WORKSPACE")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"


# ---------------------------------------------------------------------------
# Helper-Funktionen
# ---------------------------------------------------------------------------

def test_json_field_parses_string():
    """_json_field muss JSON-String korrekt parsen."""
    import services.api.main as api

    result = api._json_field('["a", "b"]', [])
    assert result == ["a", "b"]


def test_json_field_returns_fallback_on_invalid():
    """_json_field muss Fallback bei ungültigem JSON zurückgeben."""
    import services.api.main as api

    result = api._json_field("not-json", [])
    assert result == []


def test_json_field_returns_fallback_on_none():
    """_json_field muss Fallback bei None zurückgeben."""
    import services.api.main as api

    result = api._json_field(None, {})
    assert result == {}
