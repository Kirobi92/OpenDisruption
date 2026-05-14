"""
Unit-Tests für services/image-generation/main.py
Zone: WORKSPACE

asyncpg-Pool, httpx-Calls (Ollama) und Dateisystem-Operationen werden vollständig gemockt.
Kein laufender Service, keine Datenbank, kein Ollama erforderlich.
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

def _make_image_row(
    image_id: str = "img-1",
    zone: str = "WORKSPACE",
    prompt: str = "a cat",
) -> dict:
    """Erstellt eine Fake-DB-Zeile für generated_images."""
    return {
        "id": image_id,
        "prompt": prompt,
        "model_used": "llava:7b",
        "file_path": f"/data/images/{zone}/{image_id}.png",
        "zone": zone,
        "width": 512,
        "height": 512,
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
    """Erstellt einen Mock für eine erfolgreiche Ollama /api/tags Antwort."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"models": [{"name": m} for m in (models or ["llava:7b"])]}
    return resp


def _make_ollama_generate_response(response_text: str = "generated image") -> MagicMock:
    """Erstellt einen Mock für eine erfolgreiche Ollama /api/generate Antwort."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"response": response_text, "images": None}
    return resp


def _make_mock_async_client(get_resp=None, post_resp=None) -> AsyncMock:
    """Erstellt einen Mock für httpx.AsyncClient als Async-Context-Manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    if get_resp is not None:
        mock_client.get = AsyncMock(return_value=get_resp)
    if post_resp is not None:
        mock_client.post = AsyncMock(return_value=post_resp)
    return mock_client


def _make_mock_storage():
    """Erstellt einen Mock für IMAGE_STORAGE_PATH."""
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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    TestClient mit gemocktem asyncpg-Pool, Ollama-httpx-Calls und Dateisystem.
    """
    import services.image_generation.main as svc

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    with patch("services.image_generation.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)), \
         patch("services.image_generation.main.IMAGE_STORAGE_PATH", _make_mock_storage()):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            svc.db_pool = mock_pool
            yield c, mock_conn

    svc.db_pool = None


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health muss 'healthy' zurückgeben wenn DB und Ollama erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    mock_client = _make_mock_async_client(get_resp=_make_ollama_tags_response())

    with patch("services.image_generation.main.httpx.AsyncClient", return_value=mock_client):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "image-generation"
    assert data["port"] == 8011
    assert data["database"]["ok"] is True
    assert data["ollama"]["reachable"] is True


def test_health_degraded_when_ollama_down(client):
    """GET /health muss 'degraded' zurückgeben wenn Ollama nicht erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    mock_client = _make_mock_async_client()
    mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

    with patch("services.image_generation.main.httpx.AsyncClient", return_value=mock_client):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["ollama"]["reachable"] is False


def test_health_db_error_returns_degraded(client):
    """GET /health muss 'degraded' zurückgeben wenn DB nicht erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB connection failed"))

    mock_client = _make_mock_async_client(get_resp=_make_ollama_tags_response())

    with patch("services.image_generation.main.httpx.AsyncClient", return_value=mock_client):
        resp = c.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database"]["ok"] is False
    assert "DB connection failed" in data["database"]["error"]


# ---------------------------------------------------------------------------
# POST /generate
# ---------------------------------------------------------------------------

def test_generate_image_success(client):
    """POST /generate muss 201 zurückgeben und Bild-Metadaten liefern."""
    c, mock_conn = client

    image_row = _make_image_row()
    mock_conn.fetchrow = AsyncMock(return_value=image_row)

    mock_client = _make_mock_async_client(post_resp=_make_ollama_generate_response())

    with patch("services.image_generation.main.httpx.AsyncClient", return_value=mock_client), \
         patch("services.image_generation.main.IMAGE_STORAGE_PATH", _make_mock_storage()):
        resp = c.post("/generate", json={
            "prompt": "a cat",
            "model": "llava:7b",
            "zone": "WORKSPACE",
            "width": 512,
            "height": 512,
        })

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "img-1"
    assert data["zone"] == "WORKSPACE"
    assert data["model"] == "llava:7b"


def test_generate_image_fallback_when_torch_unavailable(client):
    """POST /generate muss 201 zurückgeben und Placeholder nutzen wenn torch nicht verfügbar."""
    c, mock_conn = client

    image_row = _make_image_row()
    mock_conn.fetchrow = AsyncMock(return_value=image_row)

    with patch("services.image_generation.main.IMAGE_STORAGE_PATH", _make_mock_storage()):
        resp = c.post("/generate", json={
            "prompt": "a cat",
            "model": "sdxl-turbo",
            "zone": "WORKSPACE",
        })

    # Torch ist in der Test-Umgebung nicht installiert → Placeholder-PNG, aber kein Fehler
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "img-1"
    assert data["zone"] == "WORKSPACE"


def test_generate_image_saves_to_db(client):
    """POST /generate muss einen DB-Eintrag anlegen (fetchrow aufgerufen)."""
    c, mock_conn = client

    image_row = _make_image_row()
    mock_conn.fetchrow = AsyncMock(return_value=image_row)

    mock_client = _make_mock_async_client(post_resp=_make_ollama_generate_response())

    with patch("services.image_generation.main.httpx.AsyncClient", return_value=mock_client), \
         patch("services.image_generation.main.IMAGE_STORAGE_PATH", _make_mock_storage()):
        resp = c.post("/generate", json={"prompt": "a dog", "zone": "WORKSPACE"})

    assert resp.status_code == 201
    mock_conn.fetchrow.assert_called_once()
    call_args = mock_conn.fetchrow.call_args[0]
    assert "INSERT INTO generated_images" in call_args[0]


# ---------------------------------------------------------------------------
# GET /images
# ---------------------------------------------------------------------------

def test_list_images_empty(client):
    """GET /images muss leere Liste zurückgeben wenn keine Bilder vorhanden."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[])

    resp = c.get("/images")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_images_with_zone_filter(client):
    """GET /images?zone=WORKSPACE muss nach Zone filtern."""
    c, mock_conn = client
    mock_conn.fetch = AsyncMock(return_value=[_make_image_row(zone="WORKSPACE")])

    resp = c.get("/images?zone=WORKSPACE")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "WORKSPACE"
    # Prüfe dass zone-Parameter an DB übergeben wurde
    call_args = mock_conn.fetch.call_args[0]
    assert "WHERE zone = $1" in call_args[0]


# ---------------------------------------------------------------------------
# GET /images/{image_id}
# ---------------------------------------------------------------------------

def test_get_image_not_found_returns_404(client):
    """GET /images/{id} muss 404 zurückgeben wenn Bild nicht gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.get("/images/nonexistent-id")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_get_image_found(client):
    """GET /images/{id} muss Bild-Metadaten zurückgeben wenn gefunden."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=_make_image_row(image_id="img-42"))

    resp = c.get("/images/img-42")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "img-42"
    assert data["zone"] == "WORKSPACE"
    assert data["prompt"] == "a cat"
    assert isinstance(data["metadata"], dict)
