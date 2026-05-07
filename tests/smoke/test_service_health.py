"""Smoke-Tests: /health Endpunkte aller OpenDisruption-Services.

Jeder Test prüft einen einzelnen Service. Ist der Service nicht erreichbar,
wird der Test mit ``pytest.skip`` übersprungen (kein Fail).

Ausnahme: ``test_all_critical_services_healthy`` schlägt WIRKLICH fehl,
wenn auth, api oder postgres nicht erreichbar sind.

Ausführung:
    python -m pytest tests/smoke/ -v --tb=short -m smoke
"""

from __future__ import annotations

from typing import Final

import httpx
import pytest

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

TIMEOUT: Final[float] = 5.0  # Sekunden

SERVICES: Final[dict[str, int]] = {
    "voice": 8001,
    "auth": 8002,
    "api": 8003,
    "embeddings": 8004,
    "telegram": 8005,
    "retrieval": 8006,
    "ingest": 8007,
    "model_routing": 8009,
    "image_generation": 8011,
    "media_processing": 8012,
    "web": 3002,
}

CRITICAL_SERVICES: Final[list[str]] = ["auth", "api"]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _check_health(url: str) -> httpx.Response:
    """Führt einen synchronen GET-Request auf ``url`` aus.

    Args:
        url: Vollständige URL des Health-Endpunkts.

    Returns:
        Das ``httpx.Response``-Objekt bei Erfolg.

    Raises:
        httpx.ConnectError: Wenn der Service nicht erreichbar ist.
        httpx.TimeoutException: Wenn der Request das Timeout überschreitet.
    """
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.get(url)


def _service_url(base: str, port: int) -> str:
    """Baut die Health-URL für einen Service zusammen."""
    # base_url enthält kein trailing slash (siehe conftest)
    # Ports werden direkt an localhost gehängt, nicht an einen Proxy-Host
    host = "http://localhost"
    return f"{host}:{port}/health"


def _skip_if_unreachable(url: str) -> None:
    """Überspringt den Test wenn der Service nicht erreichbar ist."""
    try:
        _check_health(url)
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        pytest.skip(f"Service nicht erreichbar: {url}")


# ---------------------------------------------------------------------------
# Einzelne Service-Tests
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_voice_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Voice-Service (Port 8001)."""
    url = _service_url(base_url, 8001)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Voice-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_auth_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Auth-Service (Port 8002)."""
    url = _service_url(base_url, 8002)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Auth-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_api_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des API-Service (Port 8003)."""
    url = _service_url(base_url, 8003)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"API-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_embeddings_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Embeddings-Service (Port 8004)."""
    url = _service_url(base_url, 8004)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Embeddings-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_telegram_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Telegram-Service (Port 8005)."""
    url = _service_url(base_url, 8005)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Telegram-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_retrieval_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Retrieval-Service (Port 8006)."""
    url = _service_url(base_url, 8006)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Retrieval-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_ingest_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Ingest-Service (Port 8007)."""
    url = _service_url(base_url, 8007)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Ingest-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_model_routing_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Model-Routing-Service (Port 8009)."""
    url = _service_url(base_url, 8009)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Model-Routing-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_image_generation_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Image-Generation-Service (Port 8011)."""
    url = _service_url(base_url, 8011)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Image-Generation-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_media_processing_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Media-Processing-Service (Port 8012)."""
    url = _service_url(base_url, 8012)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Media-Processing-Service antwortet mit Server-Fehler: {response.status_code}"
    )


@pytest.mark.smoke
def test_web_health(base_url: str) -> None:
    """Prüft den /health Endpunkt des Web-Service (Port 3002)."""
    url = _service_url(base_url, 3002)
    _skip_if_unreachable(url)
    response = _check_health(url)
    assert response.status_code < 500, (
        f"Web-Service antwortet mit Server-Fehler: {response.status_code}"
    )


# ---------------------------------------------------------------------------
# Aggregierter Kritischer Test
# ---------------------------------------------------------------------------


@pytest.mark.smoke
def test_all_critical_services_healthy(base_url: str) -> None:
    """Prüft dass auth + api erreichbar und gesund sind.

    Dieser Test schlägt WIRKLICH fehl (kein Skip) wenn kritische Services down sind.
    Postgres-Gesundheit wird indirekt über den API-Service geprüft
    (API startet nicht ohne funktionierende DB-Verbindung).
    """
    failures: list[str] = []

    critical_ports = {
        "auth": 8002,
        "api": 8003,
    }

    for service_name, port in critical_ports.items():
        url = f"http://localhost:{port}/health"
        try:
            response = _check_health(url)
            if response.status_code >= 500:
                failures.append(
                    f"{service_name} ({url}): HTTP {response.status_code} — Server-Fehler"
                )
        except httpx.ConnectError:
            failures.append(f"{service_name} ({url}): Verbindung abgelehnt — Service down?")
        except httpx.TimeoutException:
            failures.append(f"{service_name} ({url}): Timeout nach {TIMEOUT}s")

    if failures:
        failure_list = "\n  - ".join(failures)
        pytest.fail(
            f"Kritische Services nicht erreichbar:\n  - {failure_list}\n\n"
            "Starte den Stack mit: docker compose up -d auth api postgres"
        )
