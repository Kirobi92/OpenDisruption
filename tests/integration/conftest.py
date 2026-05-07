"""conftest.py für Integration-Tests.

Registriert den ``integration`` Marker und stellt gemeinsame Fixtures bereit.

Zone: WORKSPACE
"""

from __future__ import annotations

import pytest
import httpx


# ---------------------------------------------------------------------------
# Marker-Registrierung
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Registriert den ``integration`` Marker."""
    config.addinivalue_line(
        "markers",
        "integration: Integration-Tests — benötigen laufende Services und Datenbank",
    )


# ---------------------------------------------------------------------------
# Basis-URL Fixtures
# ---------------------------------------------------------------------------

TIMEOUT: float = 10.0


@pytest.fixture(scope="session")
def api_base() -> str:
    """Basis-URL des API-Service."""
    return "http://localhost:8003"


@pytest.fixture(scope="session")
def auth_base() -> str:
    """Basis-URL des Auth-Service."""
    return "http://localhost:8002"


# ---------------------------------------------------------------------------
# Auth-Token Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_token(auth_base: str) -> str:
    """Versucht Login mit Default-Credentials und gibt den Access-Token zurück.

    Überspringt alle Tests die dieses Fixture nutzen, wenn:
    - der Auth-Service nicht erreichbar ist
    - die Default-Credentials ungültig sind

    Returns:
        JWT Access-Token als String.
    """
    url = f"{auth_base}/login"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(
                url,
                json={"username": "admin", "password": "changeme"},
            )
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        pytest.skip(f"Auth-Service nicht erreichbar: {auth_base}")

    if response.status_code == 401:
        pytest.skip(
            "Default-Credentials (admin/changeme) ungültig — "
            "Stack läuft mit anderen Credentials oder Passwort wurde geändert. "
            "Nutze `make reset-default-password` um zurückzusetzen."
        )

    if response.status_code != 200:
        pytest.skip(
            f"Login fehlgeschlagen: HTTP {response.status_code} — {response.text[:200]}"
        )

    data = response.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("Login-Response enthält keinen access_token")

    return token
