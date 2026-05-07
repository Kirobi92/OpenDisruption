"""
Unit-Tests für services/retrieval/main.py
Zone: WORKSPACE

Qdrant und Embeddings-Service werden via httpx-Mock ersetzt.
Kein laufender Service erforderlich.
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
    TestClient für den Retrieval-Service.
    Der Service hat keinen Lifespan — httpx-Calls werden via patch gemockt.
    """
    from services.retrieval.main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_structure(client: TestClient):
    """GET /health muss ein dict mit 'status' zurückgeben."""
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Qdrant-Antwort
        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(
            return_value={"result": {"collections": [{"name": "kirobi_workspace"}]}}
        )

        # Embeddings-Antwort
        embed_resp = MagicMock()
        embed_resp.status_code = 200

        mock_http.get = AsyncMock(side_effect=[qdrant_resp, embed_resp])

        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert isinstance(data["status"], str)
    assert "service" in data
    assert "qdrant_reachable" in data
    assert "embeddings_reachable" in data
    assert "collections" in data


def test_health_endpoint_degraded_when_services_down(client: TestClient):
    """GET /health muss 'degraded' zurückgeben wenn Qdrant/Embeddings nicht erreichbar."""
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        import httpx as _httpx
        mock_http.get = AsyncMock(side_effect=_httpx.ConnectError("refused"))

        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["qdrant_reachable"] is False
    assert data["embeddings_reachable"] is False


# ---------------------------------------------------------------------------
# POST /search — Validierung
# ---------------------------------------------------------------------------

def test_search_validates_empty_query(client: TestClient):
    """POST /search mit leerer Query muss 422 zurückgeben."""
    resp = client.post(
        "/search",
        json={"query": "", "zone": "WORKSPACE"},
    )
    assert resp.status_code == 422


def test_search_validates_missing_query(client: TestClient):
    """POST /search ohne 'query'-Feld muss 422 zurückgeben."""
    resp = client.post(
        "/search",
        json={"zone": "WORKSPACE"},
    )
    assert resp.status_code == 422


def test_search_blocks_sacred_zone(client: TestClient):
    """
    POST /search mit Zone SACRED muss abgelehnt werden.

    SACRED ist nicht im erlaubten Pattern (PUBLIC|WORKSPACE|FAMILY_PRIVATE),
    daher gibt Pydantic 422 zurück — kein Zugriff auf SACRED-Daten via Retrieval.
    """
    resp = client.post(
        "/search",
        json={"query": "Geheime Daten", "zone": "SACRED"},
    )
    # Pydantic-Pattern-Validation schlägt fehl → 422
    assert resp.status_code == 422


def test_search_blocks_quarantine_zone(client: TestClient):
    """POST /search mit Zone QUARANTINE muss 422 zurückgeben (nicht im Pattern)."""
    resp = client.post(
        "/search",
        json={"query": "Quarantäne-Daten", "zone": "QUARANTINE"},
    )
    assert resp.status_code == 422


def test_search_valid_workspace_zone(client: TestClient):
    """POST /search mit WORKSPACE-Zone und gemockten Services muss 200 zurückgeben."""
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Embeddings-Service-Antwort
        embed_resp = MagicMock()
        embed_resp.status_code = 200
        embed_resp.json = MagicMock(return_value={"embedding": [0.1] * 768})

        # Qdrant-Such-Antwort
        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={"result": []})

        mock_http.post = AsyncMock(side_effect=[embed_resp, qdrant_resp])

        resp = client.post(
            "/search",
            json={"query": "Was ist OpenDisruption?", "zone": "WORKSPACE"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    assert "collection" in data
    assert "total" in data


def test_search_collection_not_allowed_for_zone(client: TestClient):
    """
    POST /search mit Collection die nicht zur Zone gehört muss 403 zurückgeben.
    kirobi_family ist nur für FAMILY_PRIVATE — nicht für WORKSPACE.
    """
    with patch("httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        # Embeddings-Service-Antwort (wird nicht erreicht, aber sicherheitshalber)
        embed_resp = MagicMock()
        embed_resp.status_code = 200
        embed_resp.json = MagicMock(return_value={"embedding": [0.1] * 768})
        mock_http.post = AsyncMock(return_value=embed_resp)

        resp = client.post(
            "/search",
            json={
                "query": "Familiendaten",
                "zone": "WORKSPACE",
                "collection": "kirobi_family",
            },
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /search — RAG-ähnliche Validierung (Query-Constraints)
# ---------------------------------------------------------------------------

def test_rag_validates_empty_query(client: TestClient):
    """
    POST /search mit leerer Query (RAG-Szenario) muss 422 zurückgeben.
    Der /search-Endpoint dient auch als RAG-Einstiegspunkt.
    """
    resp = client.post(
        "/search",
        json={"query": "", "zone": "WORKSPACE", "limit": 10},
    )
    assert resp.status_code == 422


def test_rag_blocks_sacred_zone(client: TestClient):
    """
    RAG-Anfrage mit Zone SACRED muss abgelehnt werden (422 via Pydantic-Pattern).
    Stellt sicher dass SACRED-Daten nicht über den Retrieval-Service abgerufen werden.
    """
    resp = client.post(
        "/search",
        json={"query": "Persönliche Grenzen", "zone": "SACRED", "limit": 5},
    )
    assert resp.status_code == 422


def test_search_limit_validation(client: TestClient):
    """POST /search mit limit=0 muss 422 zurückgeben (ge=1)."""
    resp = client.post(
        "/search",
        json={"query": "Test", "zone": "WORKSPACE", "limit": 0},
    )
    assert resp.status_code == 422


def test_search_limit_too_large(client: TestClient):
    """POST /search mit limit=51 muss 422 zurückgeben (le=50)."""
    resp = client.post(
        "/search",
        json={"query": "Test", "zone": "WORKSPACE", "limit": 51},
    )
    assert resp.status_code == 422
