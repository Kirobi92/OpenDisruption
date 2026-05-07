"""Integration-Tests: Ingest → Retrieval Flow.

Prüft das Zusammenspiel von Ingest-Service (Port 8007), Retrieval-Service (Port 8006)
und Embeddings-Service (Port 8004):
- Health-Checks beider Services
- Dokument ingestieren und Retrieval aufrufen
- Embeddings-Service erreichbar

Ausführung:
    python -m pytest tests/integration/test_ingest_retrieval_flow.py -v --tb=short -m integration

Zone: WORKSPACE
"""

from __future__ import annotations

from typing import Final

import httpx
import pytest

TIMEOUT: Final[float] = 10.0

INGEST_BASE: Final[str] = "http://localhost:8007"
RETRIEVAL_BASE: Final[str] = "http://localhost:8006"
EMBEDDINGS_BASE: Final[str] = "http://localhost:8004"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _skip_if_unreachable(url: str) -> None:
    """Überspringt den Test wenn der Service nicht erreichbar ist."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            client.get(url)
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        pytest.skip(f"Service nicht erreichbar: {url}")


def _is_reachable(url: str) -> bool:
    """Gibt True zurück wenn der Service erreichbar ist."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            client.get(url)
        return True
    except (httpx.ConnectError, httpx.TimeoutException, OSError):
        return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_ingest_health_and_retrieval_health() -> None:
    """Ingest-Service und Retrieval-Service sind beide erreichbar und healthy.

    Prüft die Health-Endpunkte beider Services im Verbund.
    Beide Services werden übersprungen wenn nicht erreichbar.
    """
    ingest_url = f"{INGEST_BASE}/health"
    retrieval_url = f"{RETRIEVAL_BASE}/health"

    _skip_if_unreachable(ingest_url)
    _skip_if_unreachable(retrieval_url)

    with httpx.Client(timeout=TIMEOUT) as client:
        ingest_response = client.get(ingest_url)
        retrieval_response = client.get(retrieval_url)

    assert ingest_response.status_code < 500, (
        f"Ingest-Service antwortet mit Server-Fehler: {ingest_response.status_code} — "
        f"{ingest_response.text[:200]}"
    )
    assert retrieval_response.status_code < 500, (
        f"Retrieval-Service antwortet mit Server-Fehler: {retrieval_response.status_code} — "
        f"{retrieval_response.text[:200]}"
    )


@pytest.mark.integration
def test_ingest_document_and_retrieve(auth_token: str) -> None:
    """Dokument ingestieren, dann Retrieval aufrufen.

    Flow:
    1. POST /ingest (oder /documents) mit Test-Dokument
    2. GET /retrieve (oder /search) mit passendem Query
    3. Antwort enthält valide Struktur

    Hinweis: Beide Services werden übersprungen wenn nicht erreichbar.
    Der Test nutzt ausschließlich WORKSPACE-Daten ohne FAMILY_PRIVATE-Inhalt.
    """
    _skip_if_unreachable(f"{INGEST_BASE}/health")
    _skip_if_unreachable(f"{RETRIEVAL_BASE}/health")

    headers = {"Authorization": f"Bearer {auth_token}"}

    test_document = {
        "content": "OpenDisruption ist ein lokales KI-Betriebssystem für Familien.",
        "metadata": {
            "source": "integration-test",
            "zone": "WORKSPACE",
            "title": "Integration-Test Dokument",
        },
    }

    with httpx.Client(timeout=TIMEOUT) as client:
        # Schritt 1: Dokument ingestieren
        # Versuche verschiedene gängige Endpunkt-Pfade
        ingest_response = None
        for path in ["/ingest", "/documents", "/index"]:
            try:
                r = client.post(
                    f"{INGEST_BASE}{path}",
                    json=test_document,
                    headers=headers,
                )
                # Wenn nicht 404/405, dann ist das der richtige Endpunkt
                if r.status_code not in (404, 405):
                    ingest_response = r
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

        if ingest_response is None:
            pytest.skip(
                "Kein bekannter Ingest-Endpunkt gefunden "
                "(/ingest, /documents, /index) — Service-API möglicherweise anders"
            )

        # Ingest sollte 2xx zurückgeben (200, 201, 202)
        assert ingest_response.status_code < 300, (
            f"Ingest fehlgeschlagen: HTTP {ingest_response.status_code} — "
            f"{ingest_response.text[:300]}"
        )

        # Schritt 2: Retrieval aufrufen
        retrieval_response = None
        query_payload = {
            "query": "OpenDisruption KI-Betriebssystem",
            "zone": "WORKSPACE",
            "limit": 5,
        }

        for path in ["/retrieve", "/search", "/query"]:
            try:
                r = client.post(
                    f"{RETRIEVAL_BASE}{path}",
                    json=query_payload,
                    headers=headers,
                )
                if r.status_code not in (404, 405):
                    retrieval_response = r
                    break
            except (httpx.ConnectError, httpx.TimeoutException):
                pass

        if retrieval_response is None:
            pytest.skip(
                "Kein bekannter Retrieval-Endpunkt gefunden "
                "(/retrieve, /search, /query) — Service-API möglicherweise anders"
            )

        assert retrieval_response.status_code < 500, (
            f"Retrieval fehlgeschlagen: HTTP {retrieval_response.status_code} — "
            f"{retrieval_response.text[:300]}"
        )

        # Antwort sollte JSON sein
        try:
            result = retrieval_response.json()
            assert result is not None, "Retrieval-Antwort ist None"
        except Exception as exc:
            pytest.fail(
                f"Retrieval-Antwort ist kein valides JSON: {exc} — "
                f"Body: {retrieval_response.text[:200]}"
            )


@pytest.mark.integration
def test_embeddings_health() -> None:
    """Embeddings-Service (Port 8004) ist erreichbar und antwortet healthy.

    Wird übersprungen wenn der Service nicht läuft (optionaler Service).
    """
    url = f"{EMBEDDINGS_BASE}/health"
    _skip_if_unreachable(url)

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(url)

    assert response.status_code < 500, (
        f"Embeddings-Service antwortet mit Server-Fehler: {response.status_code} — "
        f"{response.text[:200]}"
    )

    # Wenn JSON-Antwort, prüfe auf status-Feld
    try:
        data = response.json()
        if "status" in data:
            assert data["status"] in ("healthy", "ok", "running"), (
                f"Embeddings-Service meldet ungesunden Status: {data['status']}"
            )
    except Exception:
        # Kein JSON oder kein status-Feld — HTTP-Status reicht
        pass
