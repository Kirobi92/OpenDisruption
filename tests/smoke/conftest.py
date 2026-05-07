"""Smoke-Test Konfiguration für das OpenDisruption-Ökosystem.

Stellt Fixtures und Marker-Registrierung für alle Smoke-Tests bereit.
"""

from __future__ import annotations

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Registriert den 'smoke' Marker damit pytest keine Warnung wirft."""
    config.addinivalue_line(
        "markers",
        "smoke: Smoke-Tests die grundlegende Service-Erreichbarkeit prüfen",
    )


@pytest.fixture(scope="session")
def base_url() -> str:
    """Gibt die Basis-URL für alle Service-Tests zurück.

    Liest ``KIROBI_BASE_URL`` aus der Umgebung; Standard ist ``http://localhost``.
    """
    return os.environ.get("KIROBI_BASE_URL", "http://localhost").rstrip("/")
