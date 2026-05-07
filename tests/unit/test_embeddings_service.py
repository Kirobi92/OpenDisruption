"""
Unit-Tests für services/embeddings/main.py
Zone: WORKSPACE

Alle externen Abhängigkeiten (Ollama, Qdrant) werden gemockt.
Kein laufender Service erforderlich.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures — globale Clients mocken, bevor die App importiert wird
# ---------------------------------------------------------------------------

def _make_mock_clients():
    """Erstellt gemockte HTTP- und Qdrant-Clients."""
    mock_http = AsyncMock()
    mock_qdrant = AsyncMock()

    # Qdrant-Collections-Antwort für Health-Check
    mock_collections = MagicMock()
    mock_collections.collections = []
    mock_qdrant.get_collections = AsyncMock(return_value=mock_collections)
    mock_qdrant.upsert = AsyncMock(return_value=None)
    mock_qdrant.create_collection = AsyncMock(return_value=None)

    # Ollama-Health-Antwort
    health_resp = MagicMock()
    health_resp.raise_for_status = MagicMock()

    # Embedding-Antwort
    embed_resp = MagicMock()
    embed_resp.raise_for_status = MagicMock()
    embed_resp.json = MagicMock(return_value={"embedding": [0.1] * 768})

    # GET → health_resp, POST → embed_resp
    mock_http.get = AsyncMock(return_value=health_resp)
    mock_http.post = AsyncMock(return_value=embed_resp)

    return mock_http, mock_qdrant


@pytest.fixture()
def client():
    """
    Gibt einen TestClient zurück, bei dem Ollama- und Qdrant-Clients
    durch Mocks ersetzt sind.  Der Lifespan wird durch Patchen der
    Client-Konstruktoren umgangen.
    """
    import services.embeddings.main as emb

    mock_http, mock_qdrant = _make_mock_clients()

    # Lifespan-Konstruktoren patchen, damit keine echten Verbindungen entstehen
    with patch("services.embeddings.main.httpx.AsyncClient") as mock_http_cls, \
         patch("services.embeddings.main.AsyncQdrantClient") as mock_qdrant_cls:

        # AsyncClient als async context manager
        mock_http_cls.return_value = mock_http

        # Qdrant direkt
        mock_qdrant_cls.return_value = mock_qdrant

        # Clients vorab injizieren (für Endpoints die außerhalb des Lifespan laufen)
        emb.http_client = mock_http
        emb.qdrant_client = mock_qdrant

        with TestClient(emb.app, raise_server_exceptions=True) as c:
            # Nach Lifespan-Start nochmal sicherstellen (Lifespan überschreibt ggf.)
            emb.http_client = mock_http
            emb.qdrant_client = mock_qdrant
            yield c

    # Aufräumen
    emb.http_client = None
    emb.qdrant_client = None


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_structure(client: TestClient):
    """GET /health muss ein dict mit 'status' zurückgeben."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert isinstance(data["status"], str)
    # Weitere Pflichtfelder gemäß HealthResponse
    assert "ollama" in data
    assert "qdrant" in data
    assert "model" in data


# ---------------------------------------------------------------------------
# POST /embed — Validierung
# ---------------------------------------------------------------------------

def test_embed_validates_empty_text(client: TestClient):
    """POST /embed mit leerem Text muss 422 zurückgeben."""
    resp = client.post("/embed", json={"text": ""})
    assert resp.status_code == 422


def test_embed_validates_missing_text(client: TestClient):
    """POST /embed ohne 'text'-Feld muss 422 zurückgeben."""
    resp = client.post("/embed", json={})
    assert resp.status_code == 422


def test_embed_valid_text_calls_ollama(client: TestClient):
    """POST /embed mit gültigem Text muss 200 + Embedding zurückgeben."""
    resp = client.post("/embed", json={"text": "Hallo Welt"})
    assert resp.status_code == 200
    data = resp.json()
    assert "embedding" in data
    assert isinstance(data["embedding"], list)
    assert len(data["embedding"]) == 768
    assert "model" in data
    assert "dimensions" in data


# ---------------------------------------------------------------------------
# POST /embed/batch — Validierung
# ---------------------------------------------------------------------------

def test_embed_batch_validates_empty_list(client: TestClient):
    """POST /embed/batch mit leerer Liste muss 422 zurückgeben."""
    resp = client.post("/embed/batch", json={"texts": []})
    assert resp.status_code == 422


def test_embed_batch_validates_missing_field(client: TestClient):
    """POST /embed/batch ohne 'texts'-Feld muss 422 zurückgeben."""
    resp = client.post("/embed/batch", json={})
    assert resp.status_code == 422


def test_embed_batch_valid_returns_embeddings(client: TestClient):
    """POST /embed/batch mit gültigen Texten muss 200 + Liste zurückgeben."""
    resp = client.post("/embed/batch", json={"texts": ["Text A", "Text B"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "embeddings" in data
    assert data["count"] == 2
    assert len(data["embeddings"]) == 2


# ---------------------------------------------------------------------------
# POST /store — Zonen-Validierung
# ---------------------------------------------------------------------------

def test_store_validates_zone(client: TestClient):
    """POST /store mit ungültiger Zone muss 422 zurückgeben."""
    resp = client.post(
        "/store",
        json={"text": "Test-Dokument", "zone": "INVALID_ZONE"},
    )
    assert resp.status_code == 422


def test_store_valid_zones_accepted(client: TestClient):
    """Alle fünf gültigen Zonen müssen akzeptiert werden (kein 422)."""
    valid_zones = ["PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"]
    for zone in valid_zones:
        resp = client.post(
            "/store",
            json={"text": f"Dokument für Zone {zone}", "zone": zone},
        )
        assert resp.status_code in (200, 201), (
            f"Zone '{zone}' wurde unerwartet abgelehnt: {resp.status_code} — {resp.text}"
        )


def test_store_validates_empty_text(client: TestClient):
    """POST /store mit leerem Text muss 422 zurückgeben."""
    resp = client.post(
        "/store",
        json={"text": "", "zone": "WORKSPACE"},
    )
    assert resp.status_code == 422
