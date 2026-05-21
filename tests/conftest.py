"""
conftest.py — Pytest-Fixtures für Kirobi Backend Integrations-Tests
WebSocket-Simulation (ws-connect) und App-Lifecycle.

Architektur:
  - HTTP-Tests: httpx AsyncClient + ASGITransport (kein echter Port)
  - WS-Tests: uvicorn auf freiem Port (127.0.0.1) + websockets-Client
    → robusteste CI-Methode, kein ASGI-Internals-Hacking
  - KIROBI_TEST_MODE=1 unterdrückt echte Provider-Initialisierung

════════════════════════════════════════════════════════════════════════
FIXTURE-ÜBERSICHT
════════════════════════════════════════════════════════════════════════

┌─────────────────────┬──────────┬──────────────────────────────┬─────────────────────────────────────────┐
│ Fixture             │ Scope    │ Abhängigkeiten               │ Verwendungszweck                        │
├─────────────────────┼──────────┼──────────────────────────────┼─────────────────────────────────────────┤
│ event_loop_policy   │ session  │ –                            │ asyncio-Policy für gesamte Session      │
│ kirobi_app          │ session  │ –                            │ FastAPI-App (ASGI, kein TCP-Port)       │
│ live_server         │ session  │ kirobi_app                   │ uvicorn auf freiem Port (WS-Tests)      │
│ http_client         │ function │ kirobi_app                   │ AsyncClient via ASGITransport           │
│ ws_client           │ function │ live_server                  │ WebSocket-Verbindung (raw)              │
│ ws_session          │ function │ live_server                  │ WS + initiales Status-Event             │
│ html_file           │ session  │ tmp_path_factory             │ STUB — wird in Test-File überschrieben  │
│ page                │ class    │ html_file                    │ Desktop Chromium (1280×800, kein Touch) │
│ mobile_page         │ class    │ html_file                    │ Mobile Chromium (390×844, hasTouch=true)│
└─────────────────────┴──────────┴──────────────────────────────┴─────────────────────────────────────────┘

ENV-Variablen:
  KIROBI_TEST_MODE              = 1          Unterdrückt echte Provider-Initialisierung
  PLAYWRIGHT_VIEWPORT_WIDTH     = 1280/390   Desktop/Mobile Viewport-Breite
  PLAYWRIGHT_VIEWPORT_HEIGHT    = 800/844    Desktop/Mobile Viewport-Höhe
  PLAYWRIGHT_DEVICE_HAS_TOUCH   = true       Touch-Kontext für mobile_page

Parallelisierung:
  page und mobile_page nutzen SEPARATE Browser-Contexts (kein shared state).
  Jede Klasse bekommt eine eigene Playwright-Instanz → parallel-safe.

════════════════════════════════════════════════════════════════════════
"""
import asyncio
import json
import logging
import os
import socket
import threading
import time
import warnings
import pytest
import pytest_asyncio
from playwright.sync_api import sync_playwright, Page

logger = logging.getLogger(__name__)

# Patch env vor Import, damit keine echten Provider geladen werden
os.environ.setdefault("STT_PROVIDER", "whisper")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("TTS_PROVIDER", "edge")
os.environ.setdefault("KIROBI_TEST_MODE", "1")

from httpx import AsyncClient, ASGITransport


def _get_free_port() -> int:
    """Freien TCP-Port auf localhost finden."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def event_loop_policy():
    """asyncio-Policy für gesamte Test-Session."""
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session")
async def kirobi_app():
    """
    FastAPI-App-Instanz (für HTTP-Tests via ASGITransport).
    Lifespan wird per Warm-up-Request gestartet.
    """
    from backend.server import create_app
    application = create_app()

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        try:
            await client.get("/health")
        except Exception:
            pass

    yield application


@pytest_asyncio.fixture(scope="session")
async def live_server(kirobi_app):
    """
    Startet uvicorn auf einem freien Port für WS-Tests.
    Gibt (host, port) zurück.
    Session-scoped: Server läuft für alle WS-Tests.
    """
    import uvicorn

    port = _get_free_port()
    config = uvicorn.Config(
        kirobi_app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    # Server in separatem Thread starten
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Warten bis Server bereit
    for _ in range(50):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=0.2)
            s.close()
            break
        except OSError:
            time.sleep(0.1)

    yield ("127.0.0.1", port)

    server.should_exit = True
    thread.join(timeout=5)


@pytest_asyncio.fixture(scope="function")
async def http_client(kirobi_app):
    """
    AsyncClient gegen die ASGI-App — kein echter TCP-Port nötig.
    """
    transport = ASGITransport(app=kirobi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def ws_client(live_server):
    """
    WebSocket-Client-Fixture: echte WS-Verbindung gegen live_server.
    Gibt ein websockets-ClientConnection zurück.
    """
    import websockets.asyncio.client as wsc

    host, port = live_server
    async with wsc.connect(f"ws://{host}:{port}/ws") as ws:
        yield ws


@pytest_asyncio.fixture(scope="function")
async def ws_session(live_server):
    """
    Höheres Abstraktionslevel: WS verbinden + auf initiales Status-Event warten.
    Gibt (ws, initial_event) zurück.
    Timeout: 5s für initiales Event.
    """
    import websockets.asyncio.client as wsc

    host, port = live_server
    async with wsc.connect(f"ws://{host}:{port}/ws") as ws:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
            initial_event = json.loads(raw)
        except (asyncio.TimeoutError, Exception):
            initial_event = None
        yield ws, initial_event


# ── Hilfs-Utilities ────────────────────────────────────────────────────────────

async def ws_send_json(ws, payload: dict) -> None:
    """JSON-Event senden."""
    await ws.send(json.dumps(payload))


async def ws_recv_until(ws, event_type: str, timeout: float = 5.0) -> dict:
    """
    Empfängt Events bis ein Event mit `type == event_type` eintrifft.
    Wirft asyncio.TimeoutError wenn Timeout überschritten.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise asyncio.TimeoutError(f"Timeout waiting for event type '{event_type}'")
        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
        event = json.loads(raw)
        if event.get("type") == event_type:
            return event


# ── E2E Playwright Fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def html_file(tmp_path_factory):
    """
    Wird von test_keyboard_nav_e2e.py genutzt.
    Schreibt das HTML_FIXTURE als temporäre Datei.
    Import von HTML_FIXTURE erfolgt lazy (aus dem Test-Modul) um
    Zirkular-Importe zu vermeiden — conftest kann das Fixture daher
    als Weiterleitung bereitstellen, sodass test-Files die Fixture direkt nutzen können.
    Diese Fixture ist STUB — das eigentliche HTML_FIXTURE liefert der Test-File
    via session-scoped html_file Fixture dort. conftest.py exponiert hier nur
    die zentrale mobile_page Fixture.

    ⚠️  WARNUNG: Diese Fixture ist ein STUB und liefert None zurück.
    Sie muss im Test-File (z.B. test_keyboard_nav_e2e.py) durch eine
    session-scoped html_file Fixture ÜBERSCHRIEBEN werden, die eine echte
    HTML-Datei bereitstellt. Andernfalls werden page/mobile_page mit
    html_file=None aufgerufen und die Tests scheitern.
    """
    # Warnung via warnings.warn (erscheint in pytest -W all als UserWarning)
    warnings.warn(
        "html_file STUB aufgerufen ohne Überschreibung durch Test-File. "
        "Diese Fixture gibt None zurück — page/mobile_page erhalten kein HTML-File. "
        "Bitte in deinem Test-File eine session-scoped html_file Fixture definieren, "
        "die eine echte HTML-Datei zurückgibt (z.B. via tmp_path_factory).",
        UserWarning,
        stacklevel=2,
    )
    # Zusätzlich: logging.warning für CI-Logs die keine pytest-Warnings anzeigen
    logger.warning(
        "html_file STUB aufgerufen ohne Überschreibung (html_file=None). "
        "Test-File muss eine eigene html_file Fixture definieren."
    )
    return None  # Explizites None statt implizitem pass — eindeutig für Debugging


@pytest.fixture(scope="class")
def page(html_file):
    """
    Zentrale Desktop-Chromium-Playwright-Fixture für Keyboard-Navigation E2E-Tests.
    Konfigurierbar via ENV-Variablen:
      PLAYWRIGHT_VIEWPORT_WIDTH   (default: 1280)
      PLAYWRIGHT_VIEWPORT_HEIGHT  (default: 800)

    Wiederverwendbar für alle zukünftigen Desktop-Browser-Test-Module.
    Entspricht Standard Desktop-Viewport ohne Touch.

    ────────────────────────────────────────────────────────────────────────
    BEISPIEL: Smoke-Test mit schmalem Viewport (PLAYWRIGHT_VIEWPORT_WIDTH=800)
    ────────────────────────────────────────────────────────────────────────
    Viewport-Breite per ENV-Variable überschreiben — nützlich für Responsive-
    Tests oder um schmale Desktop-Layouts zu verifizieren:

        # Einmalig für einen Test-Run:
        PLAYWRIGHT_VIEWPORT_WIDTH=800 pytest tests/e2e/test_keyboard_nav_e2e.py -v

        # Kombiniert mit Höhe:
        PLAYWRIGHT_VIEWPORT_WIDTH=800 PLAYWRIGHT_VIEWPORT_HEIGHT=600 pytest tests/e2e/ -v

        # Als Shell-Export (bleibt für die gesamte Shell-Session aktiv):
        export PLAYWRIGHT_VIEWPORT_WIDTH=800
        pytest tests/e2e/test_keyboard_nav_e2e.py -v

    Der resultierende Chromium-Context hat dann viewport={'width': 800, 'height': 800}
    (Höhe bleibt default 800 wenn PLAYWRIGHT_VIEWPORT_HEIGHT nicht gesetzt wird).

    Smoke-Test-Befehl für CI/lokale Verifikation (ab Run 105 dokumentiert):
        PLAYWRIGHT_VIEWPORT_WIDTH=800 pytest tests/e2e/test_keyboard_nav_e2e.py -v -k "smoke"
    ────────────────────────────────────────────────────────────────────────
    """
    vw = int(os.environ.get("PLAYWRIGHT_VIEWPORT_WIDTH", "1280"))
    vh = int(os.environ.get("PLAYWRIGHT_VIEWPORT_HEIGHT", "800"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": vw, "height": vh},
        )
        pg = ctx.new_page()
        yield pg
        ctx.close()
        browser.close()


@pytest.fixture(scope="class")
def mobile_page(html_file):
    """
    Zentrale Mobile-Chromium-Playwright-Fixture für Touch/Swipe E2E-Tests.
    Konfigurierbar via ENV-Variablen:
      PLAYWRIGHT_DEVICE_HAS_TOUCH  (default: true)
      PLAYWRIGHT_VIEWPORT_WIDTH    (default: 390)
      PLAYWRIGHT_VIEWPORT_HEIGHT   (default: 844)

    Wiederverwendbar für alle zukünftigen Touch-Test-Module.
    Entspricht iPhone 12 Pro Viewport + Touch-Context.
    """
    has_touch = os.environ.get("PLAYWRIGHT_DEVICE_HAS_TOUCH", "true").lower() != "false"
    vw = int(os.environ.get("PLAYWRIGHT_VIEWPORT_WIDTH", "390"))
    vh = int(os.environ.get("PLAYWRIGHT_VIEWPORT_HEIGHT", "844"))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            has_touch=has_touch,
            viewport={"width": vw, "height": vh},
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
                "Mobile/15E148 Safari/604.1"
            ),
        )
        pg = ctx.new_page()
        yield pg
        ctx.close()
        browser.close()