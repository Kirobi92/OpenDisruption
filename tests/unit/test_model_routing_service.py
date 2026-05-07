"""
Unit-Tests für services/model-routing/main.py
Zone: WORKSPACE

Alle externen Abhängigkeiten (Ollama) werden gemockt.
Kein laufender Service erforderlich.
"""
from __future__ import annotations

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Hilfsfunktion: Ollama-Response mocken
# ---------------------------------------------------------------------------

def _make_ollama_models_response(model_names: list[str]) -> MagicMock:
    """Erstellt eine gemockte Ollama /api/tags Antwort."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json = MagicMock(return_value={
        "models": [{"name": n} for n in model_names]
    })
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_ollama_available():
    """Mockt Ollama mit einer Liste verfügbarer Modelle."""
    available = [
        "llama3.1:8b",
        "llama3.2:3b",
        "qwen2.5-coder:7b",
        "deepseek-r1:7b",
        "nomic-embed-text",
        "llava:7b",
    ]
    mock_resp = _make_ollama_models_response(available)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client, available


@pytest.fixture()
def mock_ollama_empty():
    """Mockt Ollama ohne verfügbare Modelle."""
    mock_resp = _make_ollama_models_response([])
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


@pytest.fixture()
def client_with_models(mock_ollama_available):
    """TestClient mit gemockten Ollama-Modellen."""
    mock_client, available = mock_ollama_available
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Modul neu laden damit Cache leer ist
        if "main" in sys.modules:
            del sys.modules["main"]
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/model-routing"))
        import main as routing_main
        # Cache zurücksetzen
        routing_main._available_models_cache = available
        from fastapi.testclient import TestClient as TC
        with TC(routing_main.app) as c:
            yield c, routing_main


@pytest.fixture()
def client_no_models(mock_ollama_empty):
    """TestClient ohne verfügbare Modelle."""
    with patch("httpx.AsyncClient", return_value=mock_ollama_empty):
        if "main" in sys.modules:
            del sys.modules["main"]
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/model-routing"))
        import main as routing_main
        routing_main._available_models_cache = []
        from fastapi.testclient import TestClient as TC
        with TC(routing_main.app) as c:
            yield c, routing_main


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_structure(self, client_with_models):
        """GET /health gibt korrekte Struktur zurück."""
        client, _ = client_with_models
        with patch("main._get_available_models", new=AsyncMock(return_value=["llama3.1:8b"])):
            resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "service" in data
        assert "ollama_reachable" in data
        assert "available_models" in data
        assert data["service"] == "kirobi-model-routing"
        assert isinstance(data["available_models"], list)

    def test_health_status_ok_when_models_available(self, client_with_models):
        """Health-Status ist 'ok' wenn Modelle verfügbar sind."""
        client, _ = client_with_models
        with patch("main._get_available_models", new=AsyncMock(return_value=["llama3.1:8b"])):
            resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert data["ollama_reachable"] is True

    def test_health_status_degraded_when_no_models(self, client_no_models):
        """Health-Status ist 'degraded' wenn keine Modelle verfügbar."""
        client, _ = client_no_models
        with patch("main._get_available_models", new=AsyncMock(return_value=[])):
            resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["ollama_reachable"] is False


class TestRouteEndpoint:
    @pytest.mark.parametrize("task_type", [
        "chat", "code", "reasoning", "embedding", "vision", "supervisor"
    ])
    def test_route_valid_task_types(self, client_with_models, task_type):
        """POST /route gibt für alle gültigen task_types eine Antwort zurück."""
        client, _ = client_with_models
        available = ["llama3.1:8b", "llama3.2:3b", "qwen2.5-coder:7b",
                     "deepseek-r1:7b", "nomic-embed-text", "llava:7b"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.post("/route", json={"task_type": task_type})
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_type"] == task_type
        assert "model" in data
        assert "fallback_model" in data
        assert "available" in data
        assert "reason" in data
        assert isinstance(data["model"], str)
        assert len(data["model"]) > 0

    def test_route_invalid_task_type(self, client_with_models):
        """POST /route mit unbekanntem task_type → 400."""
        client, _ = client_with_models
        with patch("main._get_available_models", new=AsyncMock(return_value=[])):
            resp = client.post("/route", json={"task_type": "unknown_xyz"})
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data
        assert "unknown_xyz" in data["detail"]

    def test_route_prefer_fast_selects_fallback(self, client_with_models):
        """prefer_fast=True wählt das Fallback-Modell wenn verfügbar."""
        client, _ = client_with_models
        available = ["llama3.1:8b", "llama3.2:3b"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.post("/route", json={"task_type": "chat", "prefer_fast": True})
        assert resp.status_code == 200
        data = resp.json()
        # Fallback für chat ist llama3.2:3b
        assert data["model"] == "llama3.2:3b"

    def test_route_selects_primary_when_available(self, client_with_models):
        """Primär-Modell wird gewählt wenn verfügbar und prefer_fast=False."""
        client, _ = client_with_models
        available = ["llama3.1:8b", "llama3.2:3b"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.post("/route", json={"task_type": "chat", "prefer_fast": False})
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "llama3.1:8b"

    def test_route_falls_back_when_primary_unavailable(self, client_with_models):
        """Fallback-Modell wird gewählt wenn Primär nicht verfügbar."""
        client, _ = client_with_models
        # Nur Fallback verfügbar, kein Primary
        available = ["llama3.2:3b"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.post("/route", json={"task_type": "chat"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "llama3.2:3b"

    def test_route_missing_task_type_returns_422(self, client_with_models):
        """POST /route ohne task_type → 422 Validation Error."""
        client, _ = client_with_models
        resp = client.post("/route", json={})
        assert resp.status_code == 422


class TestRoutingTableEndpoint:
    def test_routing_table_endpoint(self, client_with_models):
        """GET /routing-table gibt dict mit routing und task_types zurück."""
        client, _ = client_with_models
        resp = client.get("/routing-table")
        assert resp.status_code == 200
        data = resp.json()
        assert "routing" in data
        assert "task_types" in data
        assert isinstance(data["routing"], dict)
        assert isinstance(data["task_types"], list)
        # Alle erwarteten Task-Typen vorhanden
        expected = {"chat", "code", "reasoning", "embedding", "vision", "supervisor"}
        assert expected.issubset(set(data["task_types"]))

    def test_routing_table_contains_model_info(self, client_with_models):
        """Routing-Tabelle enthält primary/fallback/description für jeden Typ."""
        client, _ = client_with_models
        resp = client.get("/routing-table")
        data = resp.json()
        for task_type, info in data["routing"].items():
            assert "primary" in info, f"{task_type} fehlt 'primary'"
            assert "fallback" in info, f"{task_type} fehlt 'fallback'"
            assert "description" in info, f"{task_type} fehlt 'description'"


class TestListModelsEndpoint:
    def test_list_models_endpoint(self, client_with_models):
        """GET /models gibt dict mit models, count und routing_table zurück."""
        client, _ = client_with_models
        available = ["llama3.1:8b", "nomic-embed-text"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.get("/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "count" in data
        assert "routing_table" in data
        assert isinstance(data["models"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["models"])

    def test_list_models_count_matches_list(self, client_with_models):
        """count stimmt mit der Länge der models-Liste überein."""
        client, _ = client_with_models
        available = ["llama3.1:8b", "llama3.2:3b", "qwen2.5-coder:7b"]
        with patch("main._get_available_models", new=AsyncMock(return_value=available)):
            resp = client.get("/models")
        data = resp.json()
        assert data["count"] == 3
        assert len(data["models"]) == 3
