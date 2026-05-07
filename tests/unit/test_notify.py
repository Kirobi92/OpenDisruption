"""
Unit-Tests für kirobi_core/notify.py
Zone: WORKSPACE

Alle externen Abhängigkeiten (urllib, Telegram API) werden gemockt.
Kein Netzwerk-Zugriff erforderlich.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
from io import BytesIO

import pytest


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _make_urlopen_response(ok: bool = True) -> MagicMock:
    """Erstellt eine gemockte urllib-Response."""
    resp = MagicMock()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    resp.read = MagicMock(return_value=json.dumps({"ok": ok}).encode("utf-8"))
    return resp


# ---------------------------------------------------------------------------
# Tests: notify() ohne Token
# ---------------------------------------------------------------------------

class TestNotifyNoToken:
    def test_notify_no_token_returns_false(self):
        """Ohne Token gibt notify() False zurück ohne Crash."""
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_IDS": "",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            # Modul neu importieren damit _ENABLED neu berechnet wird
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            result = notify_mod.notify("Test-Nachricht")
            assert result is False

    def test_notify_no_token_does_not_call_urlopen(self):
        """Ohne Token wird kein HTTP-Request gemacht."""
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_IDS": "",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch("urllib.request.urlopen") as mock_urlopen:
                notify_mod.notify("Test")
                mock_urlopen.assert_not_called()

    def test_notify_task_done_no_token_returns_false(self):
        """notify_task_done() ohne Token gibt False zurück."""
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_IDS": "",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            result = notify_mod.notify_task_done("T1", "Test-Task", success=True)
            assert result is False

    def test_notify_task_start_no_token_returns_false(self):
        """notify_task_start() ohne Token gibt False zurück."""
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_ALLOWED_USER_IDS": "",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            result = notify_mod.notify_task_start("T1", "Test-Task")
            assert result is False


# ---------------------------------------------------------------------------
# Tests: notify() mit gemocktem urllib
# ---------------------------------------------------------------------------

class TestNotifySendsCorrectPayload:
    def test_notify_sends_correct_payload(self):
        """notify() sendet korrektes JSON-Payload an Telegram API."""
        captured_requests = []

        def fake_urlopen(req, timeout=None):
            captured_requests.append(req)
            return _make_urlopen_response(ok=True)

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test-token-123",
            "TELEGRAM_ALLOWED_USER_IDS": "987654321",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                result = notify_mod.notify("Hallo Welt")

        assert result is True
        assert len(captured_requests) == 1
        req = captured_requests[0]

        # URL prüfen
        assert "test-token-123" in req.full_url
        assert "sendMessage" in req.full_url

        # Payload prüfen
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["chat_id"] == "987654321"
        assert "Hallo Welt" in payload["text"]
        assert payload["parse_mode"] == "HTML"

    def test_notify_uses_channel_id_as_fallback(self):
        """Wenn keine User-ID gesetzt, wird TELEGRAM_NOTIFY_CHANNEL_ID verwendet."""
        captured_requests = []

        def fake_urlopen(req, timeout=None):
            captured_requests.append(req)
            return _make_urlopen_response(ok=True)

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test-token-456",
            "TELEGRAM_ALLOWED_USER_IDS": "",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "-100123456789",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                result = notify_mod.notify("Channel-Test")

        assert result is True
        payload = json.loads(captured_requests[0].data.decode("utf-8"))
        assert payload["chat_id"] == "-100123456789"

    def test_notify_returns_false_on_http_error(self):
        """notify() gibt False zurück bei HTTP-Fehler."""
        import urllib.error

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test-token-789",
            "TELEGRAM_ALLOWED_USER_IDS": "111222333",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                url="https://api.telegram.org",
                code=401,
                msg="Unauthorized",
                hdrs=None,  # type: ignore
                fp=BytesIO(b"Unauthorized"),
            )):
                result = notify_mod.notify("Fehler-Test")

        assert result is False

    def test_notify_returns_false_on_network_error(self):
        """notify() gibt False zurück bei Netzwerk-Fehler."""
        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "test-token-net",
            "TELEGRAM_ALLOWED_USER_IDS": "111222333",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch("urllib.request.urlopen", side_effect=ConnectionError("Netzwerk nicht erreichbar")):
                result = notify_mod.notify("Netzwerk-Test")

        assert result is False


# ---------------------------------------------------------------------------
# Tests: notify_task_done() Format
# ---------------------------------------------------------------------------

class TestNotifyTaskDoneFormat:
    def test_notify_task_done_success_format(self):
        """notify_task_done() mit success=True enthält ✅ und 'Erledigt'."""
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify_task_done("P0.1", "Docker Compose erweitern", success=True)

        assert len(captured_texts) == 1
        text = captured_texts[0]
        assert "✅" in text
        assert "Erledigt" in text
        assert "P0.1" in text
        assert "Docker Compose erweitern" in text

    def test_notify_task_done_failure_format(self):
        """notify_task_done() mit success=False enthält ❌ und 'Fehlgeschlagen'."""
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify_task_done("P0.2", "Fehlerhafter Task", success=False)

        text = captured_texts[0]
        assert "❌" in text
        assert "Fehlgeschlagen" in text

    def test_notify_task_done_with_detail(self):
        """notify_task_done() mit detail-Parameter enthält den Detail-Text."""
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify_task_done(
                    "P0.3", "Task mit Detail", success=True,
                    detail="Alle 5 Tests bestanden"
                )

        text = captured_texts[0]
        assert "Alle 5 Tests bestanden" in text

    def test_notify_task_done_detail_truncated_at_300(self):
        """Detail-Text wird bei 300 Zeichen abgeschnitten."""
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        long_detail = "x" * 500

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify_task_done("P0.4", "Langer Detail", success=True, detail=long_detail)

        text = captured_texts[0]
        # Maximal 300 'x' im Text
        assert text.count("x") <= 300

    def test_notify_task_start_format(self):
        """notify_task_start() enthält task_id und title."""
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify_task_start("P1.0", "Neuer Task gestartet")

        text = captured_texts[0]
        assert "P1.0" in text
        assert "Neuer Task gestartet" in text

    def test_notify_message_contains_timestamp(self):
        """notify() fügt einen Zeitstempel im Format HH:MM:SS ein."""
        import re
        captured_texts = []

        def fake_send_raw(text: str) -> bool:
            captured_texts.append(text)
            return True

        with patch.dict("os.environ", {
            "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_ALLOWED_USER_IDS": "123",
            "TELEGRAM_NOTIFY_CHANNEL_ID": "",
        }):
            import importlib
            import kirobi_core.notify as notify_mod
            importlib.reload(notify_mod)

            with patch.object(notify_mod, "_send_raw", side_effect=fake_send_raw):
                notify_mod.notify("Zeitstempel-Test")

        text = captured_texts[0]
        # Zeitstempel HH:MM:SS im Text
        assert re.search(r"\d{2}:\d{2}:\d{2}", text), f"Kein Zeitstempel in: {text}"
