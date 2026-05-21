"""
Unit-Tests für services/api/main.py
Zone: WORKSPACE

asyncpg-Pool und httpx-Calls (Auth-Service, Ollama) werden vollständig gemockt.
Auth-Dependency wird durch einen Override ersetzt.
Kein laufender Service oder Datenbank erforderlich.
"""
from __future__ import annotations

import json
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
        "original_filename": "original-test.txt",
        "file_path": "/data/uploads/testuser/workspace/test.txt",
        "file_size": 100,
        "mime_type": "text/plain",
        "zone": zone,
        "processed": True,
        "metadata": json.dumps({"ingest_status": "local-search-ready"}),
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


def test_health_db_returns_healthy(client):
    """GET /health/db prüft die dedizierte Dashboard-DB-Sonde."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    resp = c.get("/health/db")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_health_qdrant_returns_healthy(client):
    """GET /health/qdrant prüft den Qdrant-Upstream."""
    c, _ = client

    with patch("services.api.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        mock_client.get = AsyncMock(return_value=qdrant_resp)

        resp = c.get("/health/qdrant")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "qdrant"


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


def test_chat_runtime_options_exposes_models_and_voice(client):
    """GET /chat/runtime/options liefert sichtbare Runtime-Steuerungsdaten fürs UI."""
    c, _ = client

    with patch("services.api.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        models_resp = MagicMock()
        models_resp.status_code = 200
        models_resp.json = MagicMock(return_value={"models": ["llama3.1:8b", "deepseek-r1:7b"]})

        voice_resp = MagicMock()
        voice_resp.status_code = 200
        voice_resp.json = MagicMock(return_value={"stt_model": "whisper-small", "tts_model": "thorsten"})

        mock_client.get = AsyncMock(side_effect=[models_resp, voice_resp])

        resp = c.get("/chat/runtime/options")

    assert resp.status_code == 200
    data = resp.json()
    assert data["available_models"] == ["llama3.1:8b", "deepseek-r1:7b"]
    assert data["default_model"] == "llama3.1:8b"
    assert any(agent["id"] == "hermes" for agent in data["agent_options"])
    assert any(mode["id"] == "ultra-deep" for mode in data["reasoning_modes"])
    assert data["voice"]["available"] is True
    assert data["voice"]["stt_model"] == "whisper-small"


def test_create_message_persists_runtime_metadata_and_returns_model(client):
    """POST /conversations/{id}/messages speichert Runtime-Metadaten und sichtbare Antwortspur."""
    c, mock_conn = client
    assistant_row = _make_message_row()
    assistant_row["metadata"] = json.dumps(
        {
            "agent": "hermes",
            "reasoning_mode": "deep",
            "reasoning_label": "tiefgründig",
            "visible_reasoning_summary": ["Agent-Persona: hermes"],
            "source_trace": ["local-rag"],
        }
    )
    mock_conn.fetchrow = AsyncMock(side_effect=[_make_conversation_row(), assistant_row])
    mock_conn.fetch = AsyncMock(return_value=[])

    with patch("services.api.main._get_rag_context", AsyncMock(return_value="Lokaler Kontext")):
        with patch("services.api.main._select_chat_model", AsyncMock(return_value=("deepseek-r1:7b", "routing"))):
            with patch("services.api.main.call_ollama", AsyncMock(return_value="Analytische Antwort")):
                resp = c.post(
                    "/conversations/conv-1/messages",
                    json={
                        "content": "Analysiere das",
                        "agent": "hermes",
                        "reasoning_mode": "deep",
                        "source_modes": ["local", "deep-research"],
                        "deep_research": True,
                        "show_reasoning": True,
                    },
                )

    assert resp.status_code == 200
    data = resp.json()
    assert data["model_used"] == "llama3.1:8b"
    assert data["metadata"]["agent"] == "hermes"
    assert data["metadata"]["reasoning_mode"] == "deep"
    insert_calls = mock_conn.execute.await_args_list
    assert len(insert_calls) >= 3
    first_insert_args = insert_calls[0].args
    user_metadata = json.loads(first_insert_args[6])
    assert user_metadata["agent"] == "hermes"
    assert user_metadata["deep_research"] is True


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


def test_rag_search_proxies_retrieval_results(client):
    """POST /rag/search mappt Retrieval-/search auf das UI-Vertragsformat."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value={"can_read": True, "can_write": True})

    with patch("services.api.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        retrieval_resp = MagicMock()
        retrieval_resp.status_code = 200
        retrieval_resp.json = MagicMock(return_value={
            "query": "Kirobi",
            "collection": "kirobi_workspace",
            "total": 1,
            "results": [
                {
                    "id": "doc-1",
                    "score": 0.91,
                    "text": "Kirobi ist lokal-first.",
                    "source": "docs/kirobi.md",
                    "zone": "WORKSPACE",
                }
            ],
        })
        mock_client.post = AsyncMock(return_value=retrieval_resp)

        resp = c.post("/rag/search", json={"query": "Kirobi", "zone": "WORKSPACE"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "Kirobi"
    assert data["zone"] == "WORKSPACE"
    assert data["collection"] == "kirobi_workspace"
    assert data["results"] == [
        {
            "id": "doc-1",
            "score": 0.91,
            "source": "docs/kirobi.md",
            "zone": "WORKSPACE",
            "snippet": "Kirobi ist lokal-first.",
            "title": "kirobi.md",
            "created_at": None,
        }
    ]


def test_rag_search_requires_family_private_approval(client):
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value={"can_read": True})

    resp = c.post("/rag/search", json={"query": "Kirobi", "zone": "FAMILY_PRIVATE"})

    assert resp.status_code == 403
    assert "approval" in resp.json()["detail"].lower()


def test_rag_search_falls_back_to_local_uploads(client):
    """POST /rag/search nutzt lokale Upload-Metadaten wenn Retrieval ausfällt."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(side_effect=[
        [
            {"zone": "WORKSPACE", "can_read": True, "can_write": True},
            {"zone": "FAMILY_PRIVATE", "can_read": True, "can_write": True},
        ],
        [
            {
                "id": "file-1",
                "original_filename": "notiz.txt",
                "file_path": "/data/uploads/testuser/workspace/notiz.txt",
                "zone": "WORKSPACE",
                "created_at": datetime.now(timezone.utc),
                "metadata": json.dumps(
                    {
                        "title": "Sprint Notiz",
                        "preview": "Kirobi MVP Suchpfad lokal.",
                        "text_content": "Kirobi MVP Suchpfad lokal.",
                    }
                ),
            }
        ],
    ])

    with patch("services.api.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(side_effect=Exception("retrieval down"))

        resp = c.post("/rag/search", json={"query": "Suchpfad"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["id"] == "upload:file-1"
    assert data["results"][0]["zone"] == "WORKSPACE"
    assert "Suchpfad" in data["results"][0]["snippet"]


def test_rag_search_refuses_sacred_zone(client):
    """POST /rag/search lehnt SACRED im MVP explizit ab."""
    c, _ = client

    resp = c.post("/rag/search", json={"query": "geheim", "zone": "SACRED"})

    assert resp.status_code == 403
    assert "not available in the MVP surface" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /uploads
# ---------------------------------------------------------------------------

def test_upload_family_private_requires_approval(client):
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value={"can_write": True})

    resp = c.post(
        "/upload",
        data={"zone": "FAMILY_PRIVATE"},
        files={"file": ("synthetic.txt", b"synthetic content", "text/plain")},
    )

    assert resp.status_code == 403
    assert "approval" in resp.json()["detail"].lower()

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
    mock_conn.fetchrow = AsyncMock(return_value={"can_read": True, "can_write": True})
    mock_conn.fetch = AsyncMock(return_value=[_make_upload_row()])

    resp = c.get("/uploads?zone=WORKSPACE")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"
    assert data[0]["original_filename"] == "original-test.txt"
    assert data[0]["metadata"]["ingest_status"] == "local-search-ready"


def test_download_upload_returns_file(client, monkeypatch, tmp_path):
    """GET /uploads/{id}/download liefert die gespeicherte Datei."""
    c, mock_conn = client
    import services.api.main as api

    monkeypatch.setattr(api, "UPLOAD_DIR", tmp_path)
    stored_file = tmp_path / "testuser" / "workspace" / "test.txt"
    stored_file.parent.mkdir(parents=True)
    stored_file.write_text("hello")

    row = _make_upload_row()
    row["file_path"] = str(stored_file)
    mock_conn.fetchrow = AsyncMock(side_effect=[row, {"can_read": True}])

    resp = c.get("/uploads/file-1/download")

    assert resp.status_code == 200
    assert resp.content == b"hello"
    assert "attachment; filename=\"original-test.txt\"" in resp.headers["content-disposition"]


def test_download_upload_rejects_paths_outside_upload_dir(client, monkeypatch, tmp_path):
    """GET /uploads/{id}/download blockt fremde Dateipfade."""
    c, mock_conn = client
    import services.api.main as api

    monkeypatch.setattr(api, "UPLOAD_DIR", tmp_path / "uploads")
    outside_file = tmp_path / "elsewhere.txt"
    outside_file.write_text("secret")

    row = _make_upload_row()
    row["file_path"] = str(outside_file)
    mock_conn.fetchrow = AsyncMock(side_effect=[row, {"can_read": True}])

    resp = c.get("/uploads/file-1/download")

    assert resp.status_code == 403


def test_tasks_returns_dashboard_shape(client):
    """GET /tasks liefert das Dashboard-kompatible Aufgabenformat."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=True)
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "id": "task-1",
            "name": "Fix contracts",
            "description": "Repair dashboard/API mismatches",
            "status": "pending",
            "priority": "high",
            "assigned_agent": "keycodi",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "metadata": json.dumps({"zone": "WORKSPACE"}),
            "last_error": None,
        }
    ])

    resp = c.get("/tasks?limit=10")

    assert resp.status_code == 200
    assert resp.json()["tasks"][0]["title"] == "Fix contracts"
    assert resp.json()["tasks"][0]["agent"] == "keycodi"
    assert resp.json()["tasks"][0]["zone"] == "WORKSPACE"
    assert "lokale" in resp.json()["tasks"][0]["operator_hint"].lower()


def test_tasks_returns_empty_when_supervisor_table_missing(client):
    """GET /tasks degradiert sauber auf leere Liste ohne supervisor_tasks."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=False)

    resp = c.get("/tasks")

    assert resp.status_code == 200
    assert resp.json() == {"tasks": []}


def test_tasks_tolerate_legacy_supervisor_schema_without_last_error(client):
    """GET /tasks fällt auf Legacy-Schema ohne last_error zurück."""
    c, mock_conn = client
    import asyncpg

    mock_conn.fetchval = AsyncMock(return_value=True)
    mock_conn.fetch = AsyncMock(side_effect=[
        asyncpg.exceptions.UndefinedColumnError('column "last_error" does not exist'),
        [
            {
                "id": "task-legacy",
                "name": "Legacy task",
                "description": "Older supervisor schema",
                "status": "pending",
                "priority": "medium",
                "assigned_agent": "kirobi-core",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "metadata": json.dumps({"zone": "WORKSPACE"}),
                "last_error": None,
            }
        ],
    ])

    resp = c.get("/tasks")

    assert resp.status_code == 200
    assert resp.json()["tasks"][0]["id"] == "task-legacy"
    assert resp.json()["tasks"][0]["last_error"] is None


def test_dashboard_activity_returns_recent_summary(client):
    """GET /dashboard/activity liefert operator-taugliche Aktivitätsdaten."""
    c, mock_conn = client
    now = datetime.now(timezone.utc)
    mock_conn.fetch = AsyncMock(return_value=[
        {
            "id": "upload:file-1",
            "surface": "knowledge",
            "kind": "indexed_upload",
            "actor": "Test User",
            "summary": "Upload: projekt.txt",
            "zone": "WORKSPACE",
            "created_at": now,
        }
    ])

    resp = c.get("/dashboard/activity?limit=5")

    assert resp.status_code == 200
    assert resp.json()["items"][0]["surface"] == "knowledge"
    assert resp.json()["items"][0]["summary"] == "Upload: projekt.txt"


def test_control_status_returns_operator_summary(client):
    """GET /control/status liefert Human-Gates, Health und Attention-Tasks."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=[True, True])
    mock_conn.fetchrow = AsyncMock(side_effect=[
        {
            "pending": 2,
            "in_progress": 1,
            "completed": 4,
            "blocked": 1,
            "dead_letter": 1,
        },
        {
            "timestamp": datetime.now(timezone.utc),
            "metadata": json.dumps({"supervisor": "healthy", "ollama": "unhealthy"}),
        },
    ])
    mock_conn.fetch = AsyncMock(side_effect=[
        [
            {
                "id": "task-1",
                "name": "Review protected task",
                "status": "blocked",
                "priority": "high",
                "assigned_agent": "kirobi-core",
                "metadata": json.dumps({"zone": "FAMILY_PRIVATE"}),
                "last_error": "Human gate required",
            }
        ],
        [
            {
                "timestamp": datetime.now(timezone.utc),
                "event_type": "task_blocked",
                "severity": "warning",
                "message": "Task task-1 blocked by routing policy",
            }
        ],
    ])

    resp = c.get("/control/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["supervisorAvailable"] is True
    assert data["queueDepth"] == 4
    assert data["attentionRequired"] == 2
    assert data["health"]["ollama"] == "unhealthy"
    assert data["attentionTasks"][0]["zone"] == "FAMILY_PRIVATE"
    assert "Human gate required" in data["attentionTasks"][0]["operator_hint"]
    assert data["recentEvents"][0]["event_type"] == "task_blocked"


def test_control_status_tolerates_legacy_supervisor_schema_without_last_error(client):
    """GET /control/status unterstützt ältere supervisor_tasks-Schemata ohne last_error."""
    c, mock_conn = client
    import asyncpg

    mock_conn.fetchval = AsyncMock(side_effect=[True, True])
    mock_conn.fetchrow = AsyncMock(side_effect=[
        {
            "pending": 1,
            "in_progress": 0,
            "completed": 0,
            "blocked": 1,
            "dead_letter": 0,
        },
        {
            "timestamp": datetime.now(timezone.utc),
            "metadata": json.dumps({"supervisor": "healthy"}),
        },
    ])
    mock_conn.fetch = AsyncMock(side_effect=[
        asyncpg.exceptions.UndefinedColumnError('column "last_error" does not exist'),
        [
            {
                "id": "task-legacy",
                "name": "Legacy blocked task",
                "status": "blocked",
                "priority": "high",
                "assigned_agent": "kirobi-core",
                "metadata": json.dumps({"zone": "FAMILY_PRIVATE"}),
                "last_error": None,
            }
        ],
        [
            {
                "timestamp": datetime.now(timezone.utc),
                "event_type": "task_blocked",
                "severity": "warning",
                "message": "Legacy task blocked",
            }
        ],
    ])

    resp = c.get("/control/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["attentionTasks"][0]["id"] == "task-legacy"
    assert data["attentionTasks"][0]["last_error"] is None
    assert "Human gate" in data["attentionTasks"][0]["operator_hint"]


def test_control_status_degrades_when_supervisor_tables_missing(client):
    """GET /control/status fällt sauber auf Guided-Idle-Modus zurück."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=[False, False])

    resp = c.get("/control/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["supervisorAvailable"] is False
    assert data["queueDepth"] == 0
    assert any("Supervisor noch nicht initialisiert" in item for item in data["operatorGuidance"])


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


# ---------------------------------------------------------------------------
# /api/sc-alerts — Unit-Tests
# ---------------------------------------------------------------------------

def test_sc_alerts_empty_wenn_datei_fehlt(client, tmp_path):
    """GET /sc-alerts muss leeres Array zurückgeben wenn sc-alert-history.json fehlt."""
    import services.api.main as api

    c, _ = client
    with patch.object(api, "_SC_ALERT_HISTORY_PATH", tmp_path / "nonexistent.json"):
        resp = c.get("/sc-alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts"] == []
    assert data["total"] == 0
    assert data["limit"] == 10


def test_sc_alerts_zwei_events(client, tmp_path):
    """GET /sc-alerts muss 2 Events korrekt zurückgeben (neueste zuerst, desc by timestamp)."""
    import services.api.main as api

    history = [
        {
            "timestamp": "2026-05-21T18:00:00+00:00",
            "run_id": 111,
            "run_started_at": "2026-05-21T17:55:00Z",
            "sc_issue_count": 2,
            "threshold": 0,
            "delta": 2,
        },
        {
            "timestamp": "2026-05-21T20:00:00+00:00",
            "run_id": 222,
            "run_started_at": "2026-05-21T19:55:00Z",
            "sc_issue_count": 1,
            "threshold": 0,
            "delta": -1,
        },
    ]
    history_file = tmp_path / "sc-alert-history.json"
    history_file.write_text(json.dumps(history), encoding="utf-8")

    c, _ = client
    with patch.object(api, "_SC_ALERT_HISTORY_PATH", history_file):
        resp = c.get("/sc-alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["limit"] == 10
    # Neueste zuerst: run_id 222 hat späteres timestamp
    assert data["alerts"][0]["run_id"] == 222
    assert data["alerts"][1]["run_id"] == 111


def test_sc_alerts_limit_1(client, tmp_path):
    """GET /sc-alerts?limit=1 muss genau 1 Event zurückgeben, total=2 bleibt."""
    import services.api.main as api

    history = [
        {
            "timestamp": "2026-05-21T18:00:00+00:00",
            "run_id": 111,
            "run_started_at": "2026-05-21T17:55:00Z",
            "sc_issue_count": 3,
            "threshold": 0,
            "delta": 3,
        },
        {
            "timestamp": "2026-05-21T20:00:00+00:00",
            "run_id": 222,
            "run_started_at": "2026-05-21T19:55:00Z",
            "sc_issue_count": 1,
            "threshold": 0,
            "delta": -2,
        },
    ]
    history_file = tmp_path / "sc-alert-history.json"
    history_file.write_text(json.dumps(history), encoding="utf-8")

    c, _ = client
    with patch.object(api, "_SC_ALERT_HISTORY_PATH", history_file):
        resp = c.get("/sc-alerts?limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["alerts"]) == 1
    assert data["total"] == 2
    assert data["limit"] == 1
    # Neueste zuerst (run_id 222)
    assert data["alerts"][0]["run_id"] == 222
