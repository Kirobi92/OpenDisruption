"""
Unit-Tests für services/retrieval/main.py
Zone: WORKSPACE

Qdrant-HTTP-Calls und Embeddings-Service-Calls werden vollständig gemockt.
Zone-Enforcement wird explizit getestet.
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
    """TestClient für den Retrieval-Service."""
    import services.retrieval.main as retrieval

    with TestClient(retrieval.app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_structure(client):
    """GET /health muss alle erwarteten Felder zurückgeben."""
    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        # Qdrant antwortet OK
        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={"result": {"collections": []}})

        # Embeddings antwortet OK
        embed_resp = MagicMock()
        embed_resp.status_code = 200

        mock_client.get = AsyncMock(side_effect=[qdrant_resp, embed_resp])

        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "kirobi-retrieval"
        assert "qdrant_reachable" in data
        assert "embeddings_reachable" in data
        assert "collections" in data


def test_health_degraded_when_services_down(client):
    """GET /health muss 'degraded' zurückgeben wenn Services nicht erreichbar."""
    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["qdrant_reachable"] is False
        assert data["embeddings_reachable"] is False


# ---------------------------------------------------------------------------
# POST /search — Zone-Enforcement
# ---------------------------------------------------------------------------

def test_search_public_zone_allowed_collection(client):
    """POST /search mit PUBLIC-Zone und erlaubter Collection muss 200 zurückgeben."""
    fake_embedding = [0.1] * 768
    qdrant_results = [
        {
            "id": "doc-1",
            "score": 0.95,
            "payload": {"text": "Relevant content", "source": "test", "zone": "PUBLIC", "tags": []},
        }
    ]

    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        # Embeddings-Service-Response
        embed_resp = MagicMock()
        embed_resp.status_code = 200
        embed_resp.json = MagicMock(return_value={"embedding": fake_embedding})

        # Qdrant-Response
        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={"result": qdrant_results})

        mock_client.post = AsyncMock(side_effect=[embed_resp, qdrant_resp])

        resp = client.post(
            "/search",
            json={
                "query": "Was ist Kirobi?",
                "zone": "PUBLIC",
                "collection": "kirobi_workspace",
                "limit": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "Was ist Kirobi?"
        assert data["collection"] == "kirobi_workspace"
        assert data["total"] == 1
        assert len(data["results"]) == 1


def test_search_family_private_collection_blocked_for_public_zone(client):
    """POST /search muss 403 zurückgeben wenn FAMILY_PRIVATE-Collection für PUBLIC-Zone angefragt."""
    resp = client.post(
        "/search",
        json={
            "query": "Familiendaten",
            "zone": "PUBLIC",
            "collection": "kirobi_family",
            "limit": 5,
        },
    )
    assert resp.status_code == 403
    assert "nicht erlaubt" in resp.json()["detail"]


def test_search_family_private_zone_allows_family_collection(client):
    """POST /search mit FAMILY_PRIVATE-Zone muss kirobi_family erlauben."""
    fake_embedding = [0.1] * 768

    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        embed_resp = MagicMock()
        embed_resp.status_code = 200
        embed_resp.json = MagicMock(return_value={"embedding": fake_embedding})

        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={"result": []})

        mock_client.post = AsyncMock(side_effect=[embed_resp, qdrant_resp])

        resp = client.post(
            "/search",
            json={
                "query": "Familienurlaub",
                "zone": "FAMILY_PRIVATE",
                "collection": "kirobi_family",
                "limit": 3,
            },
        )
        assert resp.status_code == 200


def test_search_workspace_zone_blocks_family_collection(client):
    """POST /search muss 403 zurückgeben wenn WORKSPACE-Zone kirobi_family anfragt."""
    resp = client.post(
        "/search",
        json={
            "query": "Test",
            "zone": "WORKSPACE",
            "collection": "kirobi_family",
        },
    )
    assert resp.status_code == 403


def test_search_invalid_zone_returns_422(client):
    """POST /search mit ungültiger Zone muss 422 zurückgeben."""
    resp = client.post(
        "/search",
        json={
            "query": "Test",
            "zone": "SACRED",  # Nicht in Pattern erlaubt
        },
    )
    assert resp.status_code == 422


def test_search_validates_empty_query(client):
    """POST /search mit leerem Query muss 422 zurückgeben."""
    resp = client.post(
        "/search",
        json={"query": "", "zone": "WORKSPACE"},
    )
    assert resp.status_code == 422


def test_search_validates_limit_bounds(client):
    """POST /search mit limit > 50 muss 422 zurückgeben."""
    resp = client.post(
        "/search",
        json={"query": "Test", "zone": "WORKSPACE", "limit": 100},
    )
    assert resp.status_code == 422


def test_search_returns_502_when_embeddings_fail(client):
    """POST /search muss 502 zurückgeben wenn Embeddings-Service nicht erreichbar."""
    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        embed_resp = MagicMock()
        embed_resp.status_code = 503
        mock_client.post = AsyncMock(return_value=embed_resp)

        resp = client.post(
            "/search",
            json={"query": "Test", "zone": "WORKSPACE"},
        )
        assert resp.status_code == 502


def test_search_uses_default_collection_for_zone(client):
    """POST /search ohne collection muss erste erlaubte Collection der Zone verwenden."""
    fake_embedding = [0.1] * 768

    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        embed_resp = MagicMock()
        embed_resp.status_code = 200
        embed_resp.json = MagicMock(return_value={"embedding": fake_embedding})

        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={"result": []})

        mock_client.post = AsyncMock(side_effect=[embed_resp, qdrant_resp])

        resp = client.post(
            "/search",
            json={"query": "Test", "zone": "PUBLIC"},
        )
        assert resp.status_code == 200
        # Erste Collection für PUBLIC ist kirobi_workspace
        assert resp.json()["collection"] == "kirobi_workspace"


# ---------------------------------------------------------------------------
# GET /collections
# ---------------------------------------------------------------------------

def test_list_collections_returns_structure(client):
    """GET /collections muss collections und count zurückgeben."""
    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)

        qdrant_resp = MagicMock()
        qdrant_resp.status_code = 200
        qdrant_resp.json = MagicMock(return_value={
            "result": {
                "collections": [
                    {"name": "kirobi_workspace"},
                    {"name": "kirobi_family"},
                ]
            }
        })
        mock_client.get = AsyncMock(return_value=qdrant_resp)

        resp = client.get("/collections")
        assert resp.status_code == 200
        data = resp.json()
        assert "collections" in data
        assert "count" in data
        assert data["count"] == 2


def test_list_collections_returns_empty_on_qdrant_error(client):
    """GET /collections muss leere Liste zurückgeben wenn Qdrant nicht erreichbar."""
    with patch("services.retrieval.main.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))

        resp = client.get("/collections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["collections"] == []
        assert data["count"] == 0
        assert "error" in data


# ---------------------------------------------------------------------------
# Zone-Enforcement Konstanten
# ---------------------------------------------------------------------------

def test_zone_collections_family_private_isolated():
    """FAMILY_PRIVATE-Collections dürfen nicht in PUBLIC oder WORKSPACE sein."""
    import services.retrieval.main as retrieval

    family_collections = set(retrieval.ZONE_COLLECTIONS.get("FAMILY_PRIVATE", []))
    public_collections = set(retrieval.ZONE_COLLECTIONS.get("PUBLIC", []))
    workspace_collections = set(retrieval.ZONE_COLLECTIONS.get("WORKSPACE", []))

    # kirobi_family darf nicht in PUBLIC oder WORKSPACE sein
    assert "kirobi_family" not in public_collections
    assert "kirobi_family" not in workspace_collections
    assert "kirobi_family" in family_collections
