"""
conftest.py — Playwright-Fixtures für E2E Story Navigation Tests.
Wird nur in tests/e2e/ geladen — kein Konflikt mit tests/conftest.py Bootstrap.

Playwright-Import ist optional (lazy) damit CI-Jobs ohne Playwright nicht crashen.
"""
import pytest
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore
    _PLAYWRIGHT_AVAILABLE = False


@pytest.fixture(scope="session")
def html_file(tmp_path_factory):
    """
    STUB — html_file Fixture.
    Tests überschreiben diese Fixture mit eigenem HTML-Content.
    Warnung falls STUB ohne Überschreibung aufgerufen wird.
    """
    import logging
    logging.warning(
        "html_file STUB aufgerufen ohne Test-File-Override. "
        "Bitte html_file Fixture im Test-File überschreiben."
    )
    stub = tmp_path_factory.mktemp("stub") / "stub.html"
    stub.write_text("<html><body>STUB</body></html>", encoding="utf-8")
    return stub


@pytest.fixture(scope="class")
def page(html_file):
    """
    Desktop Chromium Playwright Page (1280×800, kein Touch).
    Scope: class — wird pro Test-Klasse neu erstellt.

    ENV-Overrides:
      PLAYWRIGHT_VIEWPORT_WIDTH  (default: 1280)
      PLAYWRIGHT_VIEWPORT_HEIGHT (default: 800)

    Beispiel mit Override:
      PLAYWRIGHT_VIEWPORT_WIDTH=800 pytest tests/e2e/test_story_nav_e2e.py
    """
    import os
    width = int(os.environ.get("PLAYWRIGHT_VIEWPORT_WIDTH", 1280))
    height = int(os.environ.get("PLAYWRIGHT_VIEWPORT_HEIGHT", 800))

    if not _PLAYWRIGHT_AVAILABLE:
        pytest.skip("playwright not installed — E2E-Tests übersprungen")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            has_touch=False,
        )
        pg = context.new_page()
        pg.goto(f"file://{html_file}")
        yield pg
        context.close()
        browser.close()


@pytest.fixture(scope="class")
def mobile_page(html_file):
    """
    Mobile Chromium Playwright Page (390×844, hasTouch=true).
    Scope: class — separate Browser-Context von page Fixture (parallele Tests safe).

    ENV-Overrides:
      PLAYWRIGHT_VIEWPORT_WIDTH  (default: 390)
      PLAYWRIGHT_VIEWPORT_HEIGHT (default: 844)
    """
    import os
    width = int(os.environ.get("PLAYWRIGHT_VIEWPORT_WIDTH", 390))
    height = int(os.environ.get("PLAYWRIGHT_VIEWPORT_HEIGHT", 844))

    if not _PLAYWRIGHT_AVAILABLE:
        pytest.skip("playwright not installed — E2E-Tests übersprungen")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            has_touch=True,
        )
        pg = context.new_page()
        pg.goto(f"file://{html_file}")
        yield pg
        context.close()
        browser.close()
