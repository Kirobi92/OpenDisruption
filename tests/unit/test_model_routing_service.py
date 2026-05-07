"""
Unit-Tests für services/model-routing/main.py
Zone: WORKSPACE

Ollama-HTTP-Calls werden vollständig gemockt.
Routing-Logik (prefer_fast, primary/fallback) wird explizit getestet.
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
    """TestClient für den Model-Routing-Service."""
    import services.model_routing.main as routing

    # Lifespan-Call zu Ollama mocken
    with patch("services.model_routing.main._get_available_models", AsyncMock(return_value=[])):
        with TestClient(routing.app, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture()
def client_with_models():
    """TestClient mit vordefinierten verfügbaren Modellen."""
    import services.model_routing.main as routing

    available = ["llama3.1:8b", "llama3.2:3b", "qwen2.5-coder:7b", "nomic-embed-text"]

    with patch("services.model_routing.main._get_available_models", AsyncMock(return_value=available)):
        with TestClient(routing.app, raise_server_exceptions=False) as c:
            yield c, available


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_structure(client):
    """GET /health muss alle erwarteten Felder zurückgeben."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["service"] == "kirobi-model-routing"
    assert "ollama_reachable" in data
    assert "available_models" in data


def test_health_degraded_without_models(client):
    """GET /health muss 'degraded' zurückgeben wenn keine Modelle verfügbar."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["ollama_reachable"] is False


def test_health_ok_with_models(client_with_models):
    """GET /health muss 'ok' zurückgeben wenn Modelle verfügbar."""
    c, available = client_with_models
    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["ollama_reachable"] is True
    assert len(data["available_models"]) > 0


# ---------------------------------------------------------------------------
# POST /route — Routing-Logik
# ---------------------------------------------------------------------------

def test_route_unknown_task_type_returns_400(client):
    """POST /route mit unbekanntem task_type muss 400 zurückgeben."""
    resp = client.post("/route", json={"task_type": "unknown_task"})
    assert resp.status_code == 400
    assert "Unbekannter Task-Typ" in resp.json()["detail"]


def test_route_missing_task_type_returns_422(client):
    """POST /route ohne task_type muss 422 zurückgeben."""
    resp = client.post("/route", json={})
    assert resp.status_code == 422


def test_route_selects_primary_when_available(client_with_models):
    """POST /route muss Primär-Modell wählen wenn verfügbar."""
    c, _ = client_with_models
    resp = c.post("/route", json={"task_type": "chat"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "chat"
    assert data["model"] == "llama3.1:8b"
    assert data["available"] is True
    assert "Primär-Modell" in data["reason"]


def test_route_selects_fallback_when_primary_unavailable(client):
    """POST /route muss Fallback-Modell wählen wenn Primär nicht verfügbar."""
    import services.model_routing.main as routing

    # Nur Fallback-Modell verfügbar
    with patch(
        "services.model_routing.main._get_available_models",
        AsyncMock(return_value=["llama3.2:3b"]),
    ):
        with TestClient(routing.app, raise_server_exceptions=False) as c:
            resp = c.post("/route", json={"task_type": "chat"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["model"] == "llama3.2:3b"
            assert "Fallback" in data["reason"]


def test_route_prefer_fast_selects_fallback(client_with_models):
    """POST /route mit prefer_fast=True muss Fallback-Modell bevorzugen."""
    c, _ = client_with_models
    resp = c.post("/route", json={"task_type": "chat", "prefer_fast": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "llama3.2:3b"
    assert "prefer_fast" in data["reason"]


def test_route_code_task_selects_code_model(client_with_models):
    """POST /route für code-Task muss Code-Modell wählen."""
    c, _ = client_with_models
    resp = c.post("/route", json={"task_type": "code"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "code"
    assert data["model"] == "qwen2.5-coder:7b"


def test_route_embedding_task(client_with_models):
    """POST /route für embedding-Task muss Embedding-Modell wählen."""
    c, _ = client_with_models
    resp = c.post("/route", json={"task_type": "embedding"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "embedding"
    assert data["model"] == "nomic-embed-text"


def test_route_returns_fallback_model_field(client_with_models):
    """POST /route muss immer fallback_model zurückgeben."""
    c, _ = client_with_models
    resp = c.post("/route", json={"task_type": "reasoning"})
    assert resp.status_code == 200
    data = resp.json()
    assert "fallback_model" in data
    assert data["fallback_model"] == "llama3.1:8b"


def test_route_no_models_available_uses_primary_as_default(client):
    """POST /route ohne verfügbare Modelle muss trotzdem Antwort geben."""
    resp = client.post("/route", json={"task_type": "chat"})
    assert resp.status_code == 200
    data = resp.json()
    # Kein Modell verfügbar → primary wird zurückgegeben
    assert "model" in data
    assert data["available"] is False


def test_route_all_task_types_are_valid(client_with_models):
    """POST /route muss alle definierten Task-Typen akzeptieren."""
    c, _ = client_with_models
    import services.model_routing.main as routing

    for task_type in routing.MODEL_ROUTING.keys():
        resp = c.post("/route", json={"task_type": task_type})
        assert resp.status_code == 200, f"Task-Typ '{task_type}' sollte akzeptiert werden"


def test_route_with_agent_field(client_with_models):
    """POST /route mit agent-Feld muss 200 zurückgeben."""
    c, _ = client_with_models
    resp = c.post(
        "/route",
        json={"task_type": "chat", "agent": "kirobi-coder"},
    )
    assert resp.status_code == 200


def test_route_context_length_validation(client):
    """POST /route mit negativer context_length muss 422 zurückgeben."""
    resp = client.post(
        "/route",
        json={"task_type": "chat", "context_length": -1},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /models
# ---------------------------------------------------------------------------

def test_list_models_returns_structure(client_with_models):
    """GET /models muss models, count und routing_table zurückgeben."""
    c, available = client_with_models
    resp = c.get("/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "count" in data
    assert "routing_table" in data
    assert data["count"] == len(available)


def test_list_models_empty_when_ollama_down(client):
    """GET /models muss leere Liste zurückgeben wenn Ollama nicht erreichbar."""
    resp = client.get("/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["models"] == []
    assert data["count"] == 0


# ---------------------------------------------------------------------------
# GET /routing-table
# ---------------------------------------------------------------------------

def test_routing_table_returns_all_task_types(client):
    """GET /routing-table muss alle Task-Typen zurückgeben."""
    resp = client.get("/routing-table")
    assert resp.status_code == 200
    data = resp.json()
    assert "routing" in data
    assert "task_types" in data

    expected_types = {"chat", "code", "reasoning", "embedding", "vision", "supervisor"}
    assert expected_types.issubset(set(data["task_types"]))


def test_routing_table_each_entry_has_primary_and_fallback(client):
    """GET /routing-table muss für jeden Task-Typ primary und fallback enthalten."""
    resp = client.get("/routing-table")
    data = resp.json()

    for task_type, config in data["routing"].items():
        assert "primary" in config, f"{task_type} muss primary haben"
        assert "fallback" in config, f"{task_type} muss fallback haben"
        assert "description" in config, f"{task_type} muss description haben"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def test_model_routing_table_is_complete():
    """MODEL_ROUTING muss alle erwarteten Task-Typen enthalten."""
    import services.model_routing.main as routing

    expected = {"chat", "code", "reasoning", "embedding", "vision", "supervisor"}
    assert expected.issubset(set(routing.MODEL_ROUTING.keys()))


def test_model_routing_entries_have_required_fields():
    """Jeder Eintrag in MODEL_ROUTING muss primary, fallback und description haben."""
    import services.model_routing.main as routing

    for task_type, config in routing.MODEL_ROUTING.items():
        assert "primary" in config, f"{task_type}: primary fehlt"
        assert "fallback" in config, f"{task_type}: fallback fehlt"
        assert "description" in config, f"{task_type}: description fehlt"
        assert config["primary"], f"{task_type}: primary darf nicht leer sein"
        assert config["fallback"], f"{task_type}: fallback darf nicht leer sein"
