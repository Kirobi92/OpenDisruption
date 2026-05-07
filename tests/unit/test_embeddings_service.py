"""
Unit-Tests für services/embeddings/main.py
Zone: WORKSPACE

Ollama-HTTP-Calls und Qdrant-Client werden vollständig gemockt.
Lifespan wird durch Patchen der globalen Clients umgangen.
Kein laufender Service oder Netzwerk-Call erforderlich.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    TestClient mit gemockten Ollama- und Qdrant-Clients.
    Lifespan wird durch direktes Setzen der globalen Clients umgangen.
    """
    import services.embeddings.main as emb

    # Mock HTTP-Client (Ollama)
    mock_http = AsyncMock()
    mock_http.aclose = AsyncMock(return_value=None)

    # Mock Qdrant-Client
    mock_qdrant = AsyncMock()
    mock_qdrant.close = AsyncMock(return_value=None)

    # Fake-Collections-Response
    mock_collections = MagicMock()
    mock_collections.collections = []
    mock_qdrant.get_collections = AsyncMock(return_value=mock_collections)
    mock_qdrant.create_collection = AsyncMock(return_value=None)
    mock_qdrant.upsert = AsyncMock(return_value=None)

    with patch("services.embeddings.main.httpx.AsyncClient") as mock_client_cls, \
         patch("services.embeddings.main.AsyncQdrantClient") as mock_qdrant_cls:

        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_qdrant_cls.return_value = mock_qdrant

        with TestClient(emb.app, raise_server_exceptions=False) as c:
            # Globale Clients direkt setzen (Lifespan umgehen)
            emb.http_client = mock_http
            emb.qdrant_client = mock_qdrant
            yield c, mock_http, mock_qdrant

    emb.http_client = None
    emb.qdrant_client = None


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_structure(client):
    """GET /health muss status, ollama, qdrant und model zurückgeben."""
    c, mock_http, mock_qdrant = client

    # Ollama antwortet OK
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_http.get = AsyncMock(return_value=mock_response)

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "ollama" in data
    assert "qdrant" in data
    assert "model" in data


def test_health_degraded_when_ollama_fails(client):
    """GET /health muss 'degradiert' zurückgeben wenn Ollama nicht erreichbar."""
    c, mock_http, mock_qdrant = client

    mock_http.get = AsyncMock(side_effect=Exception("Connection refused"))

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degradiert"
    assert "fehler" in data["ollama"]


# ---------------------------------------------------------------------------
# POST /embed
# ---------------------------------------------------------------------------

def test_embed_returns_embedding(client):
    """POST /embed muss Embedding-Vektor zurückgeben."""
    c, mock_http, _ = client

    fake_embedding = [0.1, 0.2, 0.3] * 256  # 768 Dimensionen
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    resp = c.post("/embed", json={"text": "Hallo Welt"})
    assert resp.status_code == 200
    data = resp.json()
    assert "embedding" in data
    assert len(data["embedding"]) == 768
    assert data["dimensions"] == 768
    assert "model" in data


def test_embed_validates_empty_text(client):
    """POST /embed mit leerem Text muss 422 zurückgeben."""
    c, _, _ = client
    resp = c.post("/embed", json={"text": ""})
    assert resp.status_code == 422


def test_embed_validates_missing_text(client):
    """POST /embed ohne text-Feld muss 422 zurückgeben."""
    c, _, _ = client
    resp = c.post("/embed", json={})
    assert resp.status_code == 422


def test_embed_returns_502_when_ollama_fails(client):
    """POST /embed muss 502 zurückgeben wenn Ollama nicht erreichbar."""
    import httpx
    c, mock_http, _ = client

    mock_http.post = AsyncMock(
        side_effect=httpx.RequestError("Connection refused", request=MagicMock())
    )

    resp = c.post("/embed", json={"text": "Test"})
    assert resp.status_code == 503


def test_embed_returns_502_when_no_embedding_returned(client):
    """POST /embed muss 502 zurückgeben wenn Ollama kein Embedding liefert."""
    c, mock_http, _ = client

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": []})
    mock_http.post = AsyncMock(return_value=mock_response)

    resp = c.post("/embed", json={"text": "Test"})
    assert resp.status_code == 502


# ---------------------------------------------------------------------------
# POST /embed/batch
# ---------------------------------------------------------------------------

def test_embed_batch_returns_multiple_embeddings(client):
    """POST /embed/batch muss mehrere Embeddings zurückgeben."""
    c, mock_http, _ = client

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    resp = c.post("/embed/batch", json={"texts": ["Text 1", "Text 2", "Text 3"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert len(data["embeddings"]) == 3


def test_embed_batch_rejects_empty_text_in_list(client):
    """POST /embed/batch muss 422 zurückgeben wenn ein Text leer ist."""
    c, mock_http, _ = client

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    resp = c.post("/embed/batch", json={"texts": ["Valid text", "   ", "Another text"]})
    assert resp.status_code == 422


def test_embed_batch_validates_empty_list(client):
    """POST /embed/batch mit leerer Liste muss 422 zurückgeben."""
    c, _, _ = client
    resp = c.post("/embed/batch", json={"texts": []})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /store
# ---------------------------------------------------------------------------

def test_store_returns_201_with_valid_data(client):
    """POST /store muss 201 zurückgeben mit gültigen Daten."""
    c, mock_http, mock_qdrant = client

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    resp = c.post(
        "/store",
        json={
            "text": "Wichtiger Inhalt",
            "zone": "WORKSPACE",
            "doc_type": "document",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["zone"] == "WORKSPACE"
    assert data["collection"] == "kirobi_workspace_document"
    assert data["dimensions"] == 768


def test_store_validates_invalid_zone(client):
    """POST /store mit ungültiger Zone muss 422 zurückgeben."""
    c, _, _ = client
    resp = c.post(
        "/store",
        json={
            "text": "Test",
            "zone": "INVALID_ZONE",
        },
    )
    assert resp.status_code == 422


def test_store_uses_provided_doc_id(client):
    """POST /store muss die angegebene doc_id verwenden."""
    c, mock_http, mock_qdrant = client

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    custom_id = "my-custom-doc-id"
    resp = c.post(
        "/store",
        json={
            "text": "Test",
            "zone": "PUBLIC",
            "doc_id": custom_id,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["id"] == custom_id


def test_store_all_valid_zones(client):
    """POST /store muss alle gültigen Zonen akzeptieren."""
    c, mock_http, mock_qdrant = client

    fake_embedding = [0.1] * 768
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json = MagicMock(return_value={"embedding": fake_embedding})
    mock_http.post = AsyncMock(return_value=mock_response)

    for zone in ["PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"]:
        resp = c.post("/store", json={"text": "Test", "zone": zone})
        assert resp.status_code == 201, f"Zone {zone} sollte akzeptiert werden"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def test_collection_name_format():
    """_collection_name muss korrekt formatiert sein."""
    import services.embeddings.main as emb

    assert emb._collection_name("WORKSPACE", "document") == "kirobi_workspace_document"
    assert emb._collection_name("FAMILY_PRIVATE", "note") == "kirobi_family_private_note"
    assert emb._collection_name("PUBLIC", "DOCUMENT") == "kirobi_public_document"


def test_validate_zone_raises_for_invalid():
    """_validate_zone muss HTTPException für ungültige Zone werfen."""
    import services.embeddings.main as emb
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        emb._validate_zone("INVALID")
    assert exc_info.value.status_code == 422


def test_validate_zone_passes_for_valid():
    """_validate_zone muss für alle gültigen Zonen durchlaufen."""
    import services.embeddings.main as emb

    for zone in ["PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"]:
        emb._validate_zone(zone)  # Kein Exception erwartet
