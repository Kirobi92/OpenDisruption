"""
Unit-Tests für services/telegram/main.py
Zone: WORKSPACE

Telegram-API-Calls und DB-Calls werden vollständig gemockt.
Kein laufender Service, kein Netzwerk-Call erforderlich.
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
    TestClient für den Telegram-Service.
    Startup-Event wird durch Patchen von BOT_TOKEN und tg() umgangen.
    """
    import services.telegram.main as tg_service

    # Startup-Calls mocken damit kein echter Telegram-Call passiert
    with patch("services.telegram.main.tg", AsyncMock(return_value={"ok": True})), \
         patch("services.telegram.main.get_api_token", AsyncMock(return_value="fake-token")), \
         patch("services.telegram.main.send", AsyncMock(return_value={"ok": True})):
        with TestClient(tg_service.app, raise_server_exceptions=False) as c:
            yield c


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    """GET /health muss status='ok' zurückgeben."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "telegram-bot"


def test_health_returns_version(client):
    """GET /health muss version zurückgeben."""
    resp = client.get("/health")
    data = resp.json()
    assert "version" in data


# ---------------------------------------------------------------------------
# GET /ready
# ---------------------------------------------------------------------------

def test_ready_endpoint_returns_structure(client):
    """GET /ready muss status und config zurückgeben."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "config" in data
    assert "active_conversations" in data


def test_ready_degraded_without_config(client):
    """GET /ready muss 'degraded' zurückgeben wenn Bot-Token fehlt."""
    import services.telegram.main as tg_service

    # Ohne BOT_TOKEN ist der Service degraded
    original_token = tg_service.BOT_TOKEN
    tg_service.BOT_TOKEN = ""
    try:
        resp = client.get("/ready")
        data = resp.json()
        assert data["status"] == "degraded"
    finally:
        tg_service.BOT_TOKEN = original_token


# ---------------------------------------------------------------------------
# GET /telegram/status
# ---------------------------------------------------------------------------

def test_telegram_status_without_token(client):
    """GET /telegram/status ohne BOT_TOKEN muss degraded zurückgeben."""
    import services.telegram.main as tg_service

    original_token = tg_service.BOT_TOKEN
    tg_service.BOT_TOKEN = ""
    try:
        resp = client.get("/telegram/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["telegram"]["ok"] is False
    finally:
        tg_service.BOT_TOKEN = original_token


def test_telegram_status_with_token(client):
    """GET /telegram/status mit BOT_TOKEN ruft Telegram-API auf."""
    import services.telegram.main as tg_service

    tg_service.BOT_TOKEN = "fake-token-123"
    tg_service.TELEGRAM_API = f"https://api.telegram.org/botfake-token-123"

    with patch(
        "services.telegram.main.tg",
        AsyncMock(return_value={"ok": True, "result": {"id": 123, "username": "testbot", "first_name": "Test"}}),
    ):
        resp = client.get("/telegram/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["telegram"]["ok"] is True


# ---------------------------------------------------------------------------
# POST /telegram/webhook
# ---------------------------------------------------------------------------

def test_webhook_accepts_valid_update(client):
    """POST /telegram/webhook muss ok=True zurückgeben."""
    with patch("services.telegram.main.process_update", AsyncMock(return_value=None)):
        resp = client.post(
            "/telegram/webhook",
            json={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 12345, "type": "private"},
                    "from": {"id": 12345, "first_name": "Test"},
                    "text": "/start",
                    "date": 1700000000,
                },
            },
        )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_webhook_handles_invalid_json_gracefully(client):
    """POST /telegram/webhook mit ungültigem Body muss trotzdem 200 zurückgeben."""
    resp = client.post(
        "/telegram/webhook",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    # Fehler werden intern geloggt, Response ist immer 200
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def test_html_escapes_special_chars():
    """_html muss HTML-Sonderzeichen escapen."""
    import services.telegram.main as tg_service

    result = tg_service._html("<script>alert('xss')</script>")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_message_chunks_splits_long_text():
    """_message_chunks muss langen Text in Chunks aufteilen."""
    import services.telegram.main as tg_service

    long_text = "x" * 8000
    chunks = tg_service._message_chunks(long_text, size=3900)
    assert len(chunks) == 3
    assert all(len(c) <= 3900 for c in chunks)


def test_message_chunks_empty_string():
    """_message_chunks muss bei leerem String [''] zurückgeben."""
    import services.telegram.main as tg_service

    chunks = tg_service._message_chunks("")
    assert chunks == [""]


def test_is_authorized_empty_allowed_ids():
    """is_authorized muss False zurückgeben wenn ALLOWED_USER_IDS leer."""
    import services.telegram.main as tg_service

    original = tg_service.ALLOWED_USER_IDS
    tg_service.ALLOWED_USER_IDS = set()
    try:
        assert tg_service.is_authorized(12345) is False
    finally:
        tg_service.ALLOWED_USER_IDS = original


def test_is_authorized_with_allowed_user():
    """is_authorized muss True zurückgeben für autorisierten User."""
    import services.telegram.main as tg_service

    original = tg_service.ALLOWED_USER_IDS
    tg_service.ALLOWED_USER_IDS = {12345}
    try:
        assert tg_service.is_authorized(12345) is True
        assert tg_service.is_authorized(99999) is False
    finally:
        tg_service.ALLOWED_USER_IDS = original


def test_config_state_structure():
    """_config_state muss alle erwarteten Keys enthalten."""
    import services.telegram.main as tg_service

    config = tg_service._config_state()
    expected_keys = {
        "bot_token_configured",
        "allowed_users_configured",
        "notify_channel_configured",
        "notify_on_start",
        "webhook_configured",
        "api_token_configured",
        "api_login_configured",
        "mode",
    }
    assert expected_keys.issubset(config.keys())


def test_main_menu_keyboard_structure():
    """main_menu_keyboard muss inline_keyboard zurückgeben."""
    import services.telegram.main as tg_service

    keyboard = tg_service.main_menu_keyboard()
    assert "inline_keyboard" in keyboard
    assert len(keyboard["inline_keyboard"]) > 0


def test_back_keyboard_structure():
    """back_keyboard muss inline_keyboard mit Home-Button zurückgeben."""
    import services.telegram.main as tg_service

    keyboard = tg_service.back_keyboard()
    assert "inline_keyboard" in keyboard
    buttons = keyboard["inline_keyboard"][0]
    assert any("Hauptmenue" in b["text"] for b in buttons)
