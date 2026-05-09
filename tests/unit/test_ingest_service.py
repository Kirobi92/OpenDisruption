"""
Unit-Tests für services/ingest/main.py
Zone: WORKSPACE

asyncpg-Pool und httpx-Calls werden vollständig gemockt.
Auth-Dependency wird durch einen Override ersetzt.
Der Lifespan (DB-Verbindung, INGEST_DIR) wird via patch umgangen.
Kein laufender Service erforderlich.
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job_row(
    job_id: str = "test-job-id",
    job_status: str = "completed",
    zone: str = "WORKSPACE",
) -> dict:
    """Erstellt eine Fake-DB-Zeile für ingest_jobs."""
    return {
        "id": job_id,
        "status": job_status,
        "zone": zone,
        "source_path": f"/tmp/ingest/{zone.lower()}/{job_id}.txt",
        "source_type": "text",
        "error": None,
        "metadata": json.dumps({"title": None, "source": None}),
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    }


class _AsyncContextManagerMock:
    """Hilfsklasse: async context manager der immer dasselbe Objekt zurückgibt."""

    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    """Erstellt einen Mock-Pool der einen Mock-Connection zurückgibt."""
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=_AsyncContextManagerMock(mock_conn))
    mock_pool.close = AsyncMock(return_value=None)
    return mock_pool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path):
    """
    TestClient mit gemocktem asyncpg-Pool und Auth-Dependency-Override.
    Der Lifespan wird durch Patchen von asyncpg.create_pool und INGEST_DIR umgangen.
    """
    import services.ingest.main as ingest
    from services.ingest.main import UserInfo

    # --- asyncpg-Connection mocken ---
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)  # Standard: kein Job gefunden

    mock_pool = _make_mock_pool(mock_conn)

    # --- Auth-Dependency überschreiben ---
    fake_user = UserInfo(id="user-1", username="testuser", role="admin")

    async def _fake_auth():
        return fake_user

    ingest.app.dependency_overrides[ingest.get_current_user] = _fake_auth

    # --- Lifespan patchen: asyncpg.create_pool + INGEST_DIR ---
    with patch("services.ingest.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)), \
         patch("services.ingest.main.INGEST_DIR", tmp_path / "ingest"):

        with TestClient(ingest.app, raise_server_exceptions=False) as c:
            # db_pool nach Lifespan-Start nochmal sicherstellen
            ingest.db_pool = mock_pool
            yield c, mock_conn

    # Aufräumen
    ingest.app.dependency_overrides.clear()
    ingest.db_pool = None


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_structure(client):
    """GET /health muss ein dict mit 'status' zurückgeben."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert isinstance(data["status"], str)
    assert "service" in data
    assert data["service"] == "ingest"


# ---------------------------------------------------------------------------
# POST /ingest/text — Validierung
# ---------------------------------------------------------------------------

def test_ingest_text_validates_empty_content(client):
    """POST /ingest/text mit leerem Text muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/ingest/text",
        json={"text": "", "zone": "WORKSPACE"},
    )
    assert resp.status_code == 422


def test_ingest_text_validates_missing_text(client):
    """POST /ingest/text ohne 'text'-Feld muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/ingest/text",
        json={"zone": "WORKSPACE"},
    )
    assert resp.status_code == 422


def test_ingest_text_validates_zone(client):
    """POST /ingest/text mit ungültiger Zone muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/ingest/text",
        json={"text": "Gültiger Inhalt", "zone": "UNGUELTIGE_ZONE"},
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("zone", ["QUARANTINE", "SACRED"])
def test_ingest_text_blocks_sensitive_zones(client, zone: str):
    """POST /ingest/text muss sensible/beschränkte Zonen mit 403 blockieren."""
    c, mock_conn = client
    mock_conn.execute.reset_mock()
    resp = c.post(
        "/ingest/text",
        json={"text": "Synthetischer Testinhalt", "zone": zone},
    )
    assert resp.status_code == 403
    mock_conn.execute.assert_not_called()


def test_ingest_text_requires_explicit_family_private_approval(client):
    c, mock_conn = client
    mock_conn.execute.reset_mock()
    resp = c.post(
        "/ingest/text",
        json={"text": "Synthetischer Testinhalt", "zone": "FAMILY_PRIVATE"},
    )
    assert resp.status_code == 403
    mock_conn.execute.assert_not_called()


def test_ingest_text_allows_family_private_with_approval(client):
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_job_row(zone="FAMILY_PRIVATE"))
    resp = c.post(
        "/ingest/text",
        json={
            "text": "Synthetischer Testinhalt",
            "zone": "FAMILY_PRIVATE",
            "human_approved": True,
            "approval_note": "Lokale Familiennotiz",
        },
    )
    assert resp.status_code == 202
    assert resp.json()["zone"] == "FAMILY_PRIVATE"


def test_ingest_text_validates_missing_zone(client):
    """POST /ingest/text ohne 'zone'-Feld muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/ingest/text",
        json={"text": "Gültiger Inhalt"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /ingest/file — Zonen-Gate vor Datei-Read
# ---------------------------------------------------------------------------

def test_ingest_file_blocks_sacred_zone_before_file_read(client):
    """POST /ingest/file muss SACRED mit 403 vor DB-/Write-Pfad blockieren."""
    c, mock_conn = client
    mock_conn.execute.reset_mock()
    resp = c.post(
        "/ingest/file",
        data={"zone": "SACRED"},
        files={"file": ("synthetic.txt", b"synthetic content", "text/plain")},
    )
    assert resp.status_code == 403
    mock_conn.execute.assert_not_called()


def test_ingest_file_requires_family_private_approval(client):
    c, mock_conn = client
    mock_conn.execute.reset_mock()
    resp = c.post(
        "/ingest/file",
        data={"zone": "FAMILY_PRIVATE"},
        files={"file": ("synthetic.txt", b"synthetic content", "text/plain")},
    )
    assert resp.status_code == 403
    mock_conn.execute.assert_not_called()


# ---------------------------------------------------------------------------
# GET /ingest/status/{job_id} — 404 für unbekannte Jobs
# ---------------------------------------------------------------------------

def test_status_not_found(client):
    """GET /ingest/status/nonexistent muss 404 zurückgeben."""
    c, mock_conn = client
    # fetchrow gibt None zurück → Job nicht gefunden
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/ingest/status/nonexistent-job-id")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


def test_status_returns_job_when_found(client):
    """GET /ingest/status/{job_id} muss Job-Daten zurückgeben wenn vorhanden."""
    c, mock_conn = client
    job_id = "known-job-id"
    mock_conn.fetchrow = AsyncMock(return_value=_make_job_row(job_id=job_id))

    resp = c.get(f"/ingest/status/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "zone" in data


def test_send_to_embeddings_uses_store_with_doc_id():
    """_send_to_embeddings muss /store mit doc_id=job_id ansprechen."""
    import services.ingest.main as ingest

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("services.ingest.main.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        asyncio.run(
            ingest._send_to_embeddings(
                "job-123",
                "Synthetischer Testinhalt",
                "WORKSPACE",
                {"title": "Test"},
            )
        )

    mock_client.post.assert_awaited_once_with(
        f"{ingest.EMBEDDINGS_SERVICE_URL}/store",
        json={
            "doc_id": "job-123",
            "text": "Synthetischer Testinhalt",
            "zone": "WORKSPACE",
            "doc_type": "document",
            "metadata": {"title": "Test"},
            "family_private_approved": False,
            "approval_note": None,
        },
    )
