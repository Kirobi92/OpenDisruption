"""
Unit-Tests für services/music-generation/main.py
Zone: WORKSPACE

asyncpg-Pool, httpx-Calls (Ollama) und Dateisystem werden vollständig gemockt.
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

def _make_track_row(
    track_id: str = "track-1",
    zone: str = "WORKSPACE",
    genre: str = "ambient",
    prompt: str = "calm forest sounds",
    is_placeholder: bool = True,
) -> dict:
    return {
        "id": track_id,
        "prompt": prompt,
        "enhanced_prompt": f"Enhanced: {prompt}",
        "genre": genre,
        "duration_seconds": 30,
        "model_used": "placeholder",
        "file_path": f"/data/audio/{zone}/{track_id}.wav",
        "zone": zone,
        "is_placeholder": is_placeholder,
        "metadata": json.dumps({"ollama_host": "http://ollama:11434"}),
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


def _make_ollama_tags_response(models: list | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"models": [{"name": m} for m in (models or ["llama3.2:3b"])]}
    return resp


def _make_ollama_generate_response(text: str = "Enhanced ambient music prompt") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"response": text}
    return resp


def _make_mock_async_client(get_resp=None, post_resp=None) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    if get_resp is not None:
        mock_client.get = AsyncMock(return_value=get_resp)
    if post_resp is not None:
        mock_client.post = AsyncMock(return_value=post_resp)
    return mock_client


def _make_mock_storage():
    file_mock = MagicMock()
    file_mock.write_bytes = MagicMock()
    zone_dir = MagicMock()
    zone_dir.mkdir = MagicMock()
    zone_dir.__truediv__ = MagicMock(return_value=file_mock)
    mock_storage = MagicMock()
    mock_storage.mkdir = MagicMock()
    mock_storage.__truediv__ = MagicMock(return_value=zone_dir)
    return mock_storage


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    import services.music_generation.main as svc

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    with patch("services.music_generation.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)), \
         patch("services.music_generation.main.AUDIO_STORAGE_PATH", _make_mock_storage()):
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
    with patch("services.music_generation.main.httpx.AsyncClient", return_value=mock_http):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "music-generation"
    assert data["database"]["ok"] is True
    assert data["ollama"]["reachable"] is True


def test_health_db_error_returns_degraded(client):
    """GET /health → 'degraded' wenn DB-Fehler."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))

    mock_http = _make_mock_async_client(get_resp=_make_ollama_tags_response())
    with patch("services.music_generation.main.httpx.AsyncClient", return_value=mock_http):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database"]["ok"] is False


# ---------------------------------------------------------------------------
# POST /generate
# ---------------------------------------------------------------------------

def test_generate_track_success(client):
    """POST /generate → 201 und GeneratedTrackResponse."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_track_row())

    mock_http = _make_mock_async_client(post_resp=_make_ollama_generate_response())
    with patch("services.music_generation.main.httpx.AsyncClient", return_value=mock_http), \
         patch("services.music_generation.main.AUDIO_STORAGE_PATH", _make_mock_storage()):
        resp = c.post("/generate", json={
            "prompt": "calm forest sounds",
            "genre": "ambient",
            "duration_seconds": 30,
            "zone": "WORKSPACE",
        })

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "track-1"
    assert data["zone"] == "WORKSPACE"
    assert data["genre"] == "ambient"
    assert data["is_placeholder"] is True


def test_generate_track_ollama_down_uses_fallback(client):
    """POST /generate → 201 auch wenn Ollama nicht erreichbar (Fallback auf Original-Prompt)."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_track_row())

    mock_http = _make_mock_async_client()
    mock_http.post = AsyncMock(side_effect=Exception("Connection refused"))
    with patch("services.music_generation.main.httpx.AsyncClient", return_value=mock_http), \
         patch("services.music_generation.main.AUDIO_STORAGE_PATH", _make_mock_storage()):
        resp = c.post("/generate", json={
            "prompt": "calm forest sounds",
            "genre": "ambient",
            "duration_seconds": 30,
            "zone": "WORKSPACE",
        })

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "track-1"


# ---------------------------------------------------------------------------
# GET /tracks
# ---------------------------------------------------------------------------

def test_list_tracks_empty(client):
    """GET /tracks → leere Liste wenn keine Tracks."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/tracks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tracks_with_zone_filter(client):
    """GET /tracks?zone=WORKSPACE → gefilterte Tracks."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_track_row(zone="WORKSPACE")])

    resp = c.get("/tracks?zone=WORKSPACE")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"


# ---------------------------------------------------------------------------
# GET /tracks/{track_id}
# ---------------------------------------------------------------------------

def test_get_track_not_found_returns_404(client):
    """GET /tracks/{id} → 404 wenn Track nicht gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/tracks/nonexistent-id")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_get_track_found(client):
    """GET /tracks/{id} → TrackMetadata wenn gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_track_row(track_id="track-42"))

    resp = c.get("/tracks/track-42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "track-42"
    assert data["zone"] == "WORKSPACE"
    assert isinstance(data["metadata"], dict)


# ---------------------------------------------------------------------------
# Health — heartmula-missing Szenario (OPE-210)
# ---------------------------------------------------------------------------

def test_health_heartmula_missing(client):
    """GET /health → heartmula.available=False wenn heartlib/Modell fehlt.

    Szenario: DB ok, Ollama ok, aber heartmula-Modell-Pfad existiert nicht
    und heartlib ist nicht installiert.
    Erwartet: status='healthy' (heartmula ist optional) und
    heartmula.available=False + model_exists=False.
    """
    import services.music_generation.main as svc

    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    mock_http = _make_mock_async_client(get_resp=_make_ollama_tags_response())

    with patch("services.music_generation.main.httpx.AsyncClient", return_value=mock_http), \
         patch.object(svc, "_HEARTMULA_AVAILABLE", False), \
         patch("services.music_generation.main._HEARTMULA_MODEL_PATH") as mock_path:
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda self: "/data/models/heartmula"
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    # heartmula fehlt → Service läuft trotzdem healthy (audiocraft/heartmula optional)
    assert data["status"] == "healthy"
    assert data["heartmula"]["available"] is False
    assert data["heartmula"]["model_exists"] is False
