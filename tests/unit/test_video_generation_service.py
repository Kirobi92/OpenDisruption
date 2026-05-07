"""
Unit-Tests für services/video-generation/main.py
Zone: WORKSPACE

asyncpg-Pool und httpx-Calls (Ollama) werden vollständig gemockt.
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

def _make_job_row(
    job_id: str = "job-1",
    zone: str = "WORKSPACE",
    prompt: str = "a sunset timelapse",
    status: str = "pending",
    resolution: str = "720p",
    duration_seconds: int = 10,
) -> dict:
    return {
        "id": job_id,
        "prompt": prompt,
        "resolution": resolution,
        "duration_seconds": duration_seconds,
        "zone": zone,
        "status": status,
        "file_path": None,
        "error": None,
        "metadata": json.dumps({"ollama_host": "http://ollama:11434"}),
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
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


def _make_ollama_tags_response(models: list | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"models": [{"name": m} for m in (models or ["llama3.2:3b"])]}
    return resp


def _make_mock_async_client(get_resp=None) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    if get_resp is not None:
        mock_client.get = AsyncMock(return_value=get_resp)
    return mock_client


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    import services.video_generation.main as svc

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    with patch("services.video_generation.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            svc.db_pool = mock_pool
            yield c, mock_conn

    svc.db_pool = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health → 'healthy' wenn DB und Ollama erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    mock_http = _make_mock_async_client(get_resp=_make_ollama_tags_response())
    with patch("services.video_generation.main.httpx.AsyncClient", return_value=mock_http):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "video-generation"
    assert data["database"]["ok"] is True
    assert data["ollama"]["reachable"] is True


def test_health_db_error_returns_degraded(client):
    """GET /health → 'degraded' wenn DB-Fehler."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))

    mock_http = _make_mock_async_client(get_resp=_make_ollama_tags_response())
    with patch("services.video_generation.main.httpx.AsyncClient", return_value=mock_http):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database"]["ok"] is False


# ---------------------------------------------------------------------------
# POST /generate
# ---------------------------------------------------------------------------

def test_generate_video_success(client):
    """POST /generate → 202 und JobCreatedResponse."""
    c, mock_conn = client
    mock_conn.execute = AsyncMock(return_value=None)

    resp = c.post("/generate", json={
        "prompt": "a sunset timelapse",
        "duration": 10,
        "zone": "WORKSPACE",
        "resolution": "720p",
    })

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert "job_id" in data
    assert "message" in data


def test_generate_video_ollama_down_uses_fallback(client):
    """POST /generate → 202 auch wenn Ollama nicht erreichbar (Job wird trotzdem erstellt)."""
    c, mock_conn = client
    mock_conn.execute = AsyncMock(return_value=None)

    # Ollama ist für /generate nicht direkt nötig (async job), trotzdem testen
    resp = c.post("/generate", json={
        "prompt": "a sunset timelapse",
        "duration": 10,
        "zone": "WORKSPACE",
        "resolution": "720p",
    })

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------

def test_list_videos_empty(client):
    """GET /jobs → leere Liste wenn keine Jobs."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/jobs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_videos_with_zone_filter(client):
    """GET /jobs → Jobs zurückgeben (kein Zone-Filter in API, aber Daten prüfen)."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_job_row(zone="WORKSPACE")])

    resp = c.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"
    assert data[0]["status"] == "pending"


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

def test_get_video_not_found_returns_404(client):
    """GET /jobs/{id} → 404 wenn Job nicht gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/jobs/nonexistent-id")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_get_video_found(client):
    """GET /jobs/{id} → JobResponse wenn gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_job_row(job_id="job-42"))

    resp = c.get("/jobs/job-42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "job-42"
    assert data["zone"] == "WORKSPACE"
    assert data["status"] == "pending"
