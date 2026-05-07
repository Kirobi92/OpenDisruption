"""
Unit-Tests für services/api/main.py
Zone: WORKSPACE

Strategie:
- UPLOAD_DIR.mkdir() wird via patch("pathlib.Path.mkdir") umgangen,
  da /data/uploads im Test-Kontext nicht existiert.
- asyncpg.create_pool wird durch AsyncMock ersetzt.
- get_current_user wird via app.dependency_overrides überschrieben.
- TestClient ohne lifespan-Context (db_pool direkt gesetzt).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_mock_pool():
    """Erstellt einen asyncpg.Pool-Mock."""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=1)
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])

    pool = MagicMock()
    pool.close = AsyncMock(return_value=None)

    acquire_ctx = MagicMock()
    acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
    acquire_ctx.__aexit__ = AsyncMock(return_value=False)
    pool.acquire = MagicMock(return_value=acquire_ctx)

    return pool, conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_app():
    """Importiert services.api.main einmalig mit gemockten Dependencies."""
    mock_pool, mock_conn = _make_mock_pool()

    # Modul-Level mkdir patchen, damit /data/uploads nicht angelegt wird
    with patch("pathlib.Path.mkdir", return_value=None):
        with patch("asyncpg.create_pool", new=AsyncMock(return_value=mock_pool)):
            if "services.api.main" in sys.modules:
                del sys.modules["services.api.main"]
            if "services.api" in sys.modules:
                del sys.modules["services.api"]

            import services.api.main as api_main

            api_main.db_pool = mock_pool
            yield api_main, mock_pool, mock_conn


@pytest.fixture()
def api_client(api_app):
    """TestClient ohne Auth-Override (für 401-Tests)."""
    from fastapi.testclient import TestClient
    api_main, mock_pool, mock_conn = api_app
    api_main.db_pool = mock_pool

    client = TestClient(api_main.app, raise_server_exceptions=False)
    yield client, api_main, mock_pool, mock_conn


@pytest.fixture()
def api_client_authed(api_app):
    """TestClient mit überschriebener Auth-Dependency (fake user)."""
    from fastapi.testclient import TestClient
    api_main, mock_pool, mock_conn = api_app
    api_main.db_pool = mock_pool

    fake_user = api_main.User(
        id="test-user-id",
        username="testuser",
        display_name="Test User",
        role="family_member",
    )

    async def override_get_current_user():
        return fake_user

    api_main.app.dependency_overrides[api_main.get_current_user] = override_get_current_user

    client = TestClient(api_main.app, raise_server_exceptions=False)
    yield client, api_main, mock_pool, mock_conn, fake_user

    api_main.app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_endpoint(self, api_client):
        """GET /health → 200"""
        client, api_main, mock_pool, mock_conn = api_client
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestConversationsRequireAuth:
    def test_conversations_requires_auth(self, api_client):
        """GET /conversations ohne Token → 401"""
        client, *_ = api_client
        response = client.get("/conversations")
        assert response.status_code == 401

    def test_create_conversation_requires_auth(self, api_client):
        """POST /conversations ohne Token → 401"""
        client, *_ = api_client
        response = client.post("/conversations", json={"title": "Test", "zone": "WORKSPACE"})
        assert response.status_code == 401

    def test_messages_requires_auth(self, api_client):
        """GET /conversations/x/messages ohne Token → 401"""
        client, *_ = api_client
        response = client.get("/conversations/some-id/messages")
        assert response.status_code == 401

    def test_create_message_requires_auth(self, api_client):
        """POST /conversations/x/messages ohne Token → 401"""
        client, *_ = api_client
        response = client.post(
            "/conversations/some-id/messages",
            json={"content": "Hello"},
        )
        assert response.status_code == 401

    def test_uploads_requires_auth(self, api_client):
        """GET /uploads ohne Token → 401"""
        client, *_ = api_client
        response = client.get("/uploads")
        assert response.status_code == 401


class TestOllamaChatRequiresAuth:
    def test_ollama_chat_requires_auth(self, api_client):
        """POST /chat ohne Token → 401 oder 404 (kein /chat-Endpoint direkt)"""
        client, *_ = api_client
        response = client.post("/chat", json={"message": "Hello"})
        # /chat existiert nicht als eigenständiger Endpoint → 404/405
        # Falls er existiert, muss er 401 zurückgeben
        assert response.status_code in (401, 404, 405)


class TestConversationsWithAuth:
    def test_list_conversations_with_auth(self, api_client_authed):
        """GET /conversations mit Auth → 200 (leere Liste)"""
        client, api_main, mock_pool, mock_conn, fake_user = api_client_authed
        mock_conn.fetch = AsyncMock(return_value=[])
        api_main.db_pool = mock_pool
        response = client.get("/conversations")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_nonexistent_conversation_with_auth(self, api_client_authed):
        """GET /conversations/nonexistent mit Auth → 404"""
        client, api_main, mock_pool, mock_conn, fake_user = api_client_authed
        mock_conn.fetchrow = AsyncMock(return_value=None)
        api_main.db_pool = mock_pool
        response = client.get("/conversations/nonexistent-id")
        assert response.status_code == 404
