"""
tests/unit/test_analytics_client.py — Unit-Tests für kirobi_core.analytics_client

Zone: WORKSPACE
"""
from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kirobi_core.analytics_client import track, track_sync


# ---------------------------------------------------------------------------
# Hilfsfunktion: httpx-Modul mocken (lazy import in track())
# ---------------------------------------------------------------------------

def _make_httpx_module_mock() -> tuple[MagicMock, AsyncMock]:
    """
    Erstellt ein Mock-Modul für httpx, das als `import httpx` innerhalb
    von track() verwendet wird. httpx wird lazy importiert, daher muss
    sys.modules['httpx'] gepatcht werden.

    track() nutzt `async with httpx.AsyncClient(...) as client:` —
    daher muss AsyncClient() einen async Context-Manager zurückgeben,
    dessen __aenter__ den client_instance liefert.
    """
    response_mock = MagicMock()
    response_mock.status_code = 200

    client_instance = AsyncMock()
    client_instance.post = AsyncMock(return_value=response_mock)

    # AsyncClient() muss als async context manager funktionieren
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=client_instance)
    cm.__aexit__ = AsyncMock(return_value=False)

    httpx_mock = MagicMock()
    httpx_mock.AsyncClient.return_value = cm

    return httpx_mock, client_instance


# ---------------------------------------------------------------------------
# Tests: track()
# ---------------------------------------------------------------------------


def test_track_sendet_korrektes_payload():
    """track() sendet event_type, zone, timestamp und optionale Felder."""
    httpx_mock, client_mock = _make_httpx_module_mock()

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        asyncio.run(track(
            "test_event",
            zone="WORKSPACE",
            model="llama3.1:8b",
            tokens=42,
            metadata={"job_id": "abc-123"},
        ))

    client_mock.post.assert_awaited_once()
    call_args = client_mock.post.call_args
    url = call_args[0][0]
    payload = call_args[1]["json"]

    assert "events" in url
    assert payload["event_type"] == "test_event"
    assert payload["zone"] == "WORKSPACE"
    assert payload["model"] == "llama3.1:8b"
    assert payload["tokens"] == 42
    assert "timestamp" in payload
    assert payload["metadata"]["job_id"] == "abc-123"


def test_track_ohne_optionale_felder():
    """track() funktioniert auch ohne model/tokens/metadata."""
    httpx_mock, client_mock = _make_httpx_module_mock()

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        asyncio.run(track("minimal_event"))

    payload = client_mock.post.call_args[1]["json"]
    assert payload["event_type"] == "minimal_event"
    assert payload["zone"] == "WORKSPACE"
    assert "model" not in payload
    assert "tokens" not in payload
    assert "metadata" not in payload


def test_track_bei_netzwerkfehler_kein_exception():
    """track() propagiert keine Exception bei Netzwerkfehler."""
    httpx_mock = MagicMock()
    httpx_mock.AsyncClient.side_effect = Exception("Verbindung verweigert")

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        # Darf keine Exception werfen
        asyncio.run(track("test_event", zone="WORKSPACE"))


def test_track_bei_httpx_nicht_verfuegbar():
    """track() ist robust wenn httpx nicht importierbar ist."""
    # httpx aus sys.modules entfernen und ImportError simulieren
    original = sys.modules.get("httpx")
    sys.modules["httpx"] = None  # type: ignore[assignment]
    try:
        asyncio.run(track("test_event"))
    finally:
        if original is not None:
            sys.modules["httpx"] = original
        else:
            sys.modules.pop("httpx", None)


# ---------------------------------------------------------------------------
# Tests: Metadaten-Filter
# ---------------------------------------------------------------------------


def test_track_filtert_lange_strings_in_metadata():
    """Metadaten-Strings über 200 Zeichen werden herausgefiltert."""
    httpx_mock, client_mock = _make_httpx_module_mock()
    langer_string = "x" * 201
    kurzer_string = "y" * 200

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        asyncio.run(track(
            "filter_test",
            metadata={
                "lang": langer_string,
                "kurz": kurzer_string,
                "zahl": 42,
            },
        ))

    payload = client_mock.post.call_args[1]["json"]
    meta = payload["metadata"]
    assert "lang" not in meta, "Langer String sollte herausgefiltert werden"
    assert meta["kurz"] == kurzer_string
    assert meta["zahl"] == 42


def test_track_leere_metadata_wird_nicht_gesendet():
    """Leeres metadata-Dict wird nicht in den Payload aufgenommen."""
    httpx_mock, client_mock = _make_httpx_module_mock()

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        asyncio.run(track("event", metadata={}))

    payload = client_mock.post.call_args[1]["json"]
    # Leeres Dict ist falsy → wird nicht hinzugefügt
    assert "metadata" not in payload


# ---------------------------------------------------------------------------
# Tests: track_sync()
# ---------------------------------------------------------------------------


def test_track_sync_ohne_laufenden_loop():
    """track_sync() funktioniert ohne laufenden Event-Loop via asyncio.run."""
    httpx_mock, client_mock = _make_httpx_module_mock()

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        # Kein laufender Loop → asyncio.run Pfad
        track_sync("sync_event", zone="WORKSPACE")

    client_mock.post.assert_awaited_once()
    payload = client_mock.post.call_args[1]["json"]
    assert payload["event_type"] == "sync_event"


def test_track_sync_bei_fehler_kein_exception():
    """track_sync() propagiert keine Exception bei Fehler."""
    async def _raising_track(*_args, **_kwargs):
        raise Exception("Netzwerkfehler")

    with patch("kirobi_core.analytics_client.track", _raising_track):

        # Darf keine Exception werfen
        track_sync("fehler_event")


def test_track_sync_in_laufendem_loop_erstellt_task():
    """track_sync() nutzt loop.create_task wenn ein Loop läuft."""
    httpx_mock, client_mock = _make_httpx_module_mock()

    async def _run():
        with patch.dict(sys.modules, {"httpx": httpx_mock}):
            track_sync("loop_event", zone="WORKSPACE")
            # Kurz warten damit der Task ausgeführt wird
            await asyncio.sleep(0.05)

    asyncio.run(_run())
    client_mock.post.assert_awaited_once()
    payload = client_mock.post.call_args[1]["json"]
    assert payload["event_type"] == "loop_event"


# ---------------------------------------------------------------------------
# Tests: ANALYTICS_URL Konfiguration
# ---------------------------------------------------------------------------


def test_track_nutzt_analytics_url_env(monkeypatch):
    """ANALYTICS_SERVICE_URL aus Umgebungsvariable wird genutzt."""
    monkeypatch.setenv("ANALYTICS_SERVICE_URL", "http://custom-analytics:9999")

    import importlib
    import kirobi_core.analytics_client as mod
    importlib.reload(mod)

    httpx_mock, client_mock = _make_httpx_module_mock()

    with patch.dict(sys.modules, {"httpx": httpx_mock}):
        asyncio.run(mod.track("url_test"))

    url = client_mock.post.call_args[0][0]
    assert "custom-analytics:9999" in url

    # Zurücksetzen
    monkeypatch.delenv("ANALYTICS_SERVICE_URL", raising=False)
    importlib.reload(mod)
