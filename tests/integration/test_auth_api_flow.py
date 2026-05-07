"""Integration-Tests: Auth → API Flow.

Prüft das Zusammenspiel von Auth-Service (Port 8002) und API-Service (Port 8003):
- Login via /login → JWT-Token
- Authentifizierte Requests gegen /conversations
- Fehlerverhalten bei ungültigem Token
- Health-Chain über mehrere Services

Ausführung:
    python -m pytest tests/integration/test_auth_api_flow.py -v --tb=short -m integration

Zone: WORKSPACE
"""

from __future__ import annotations

from typing import Final

import httpx
import pytest

TIMEOUT: Final[float] = 10.0


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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_login_and_get_conversations(auth_base: str, api_base: str) -> None:
    """Login via /login, dann /conversations mit Token aufrufen.

    Prüft den vollständigen Auth→API Flow:
    1. POST /login → 200 + access_token
    2. GET /conversations mit Bearer-Token → 200 (Liste, ggf. leer)
    """
    _skip_if_unreachable(f"{auth_base}/health")
    _skip_if_unreachable(f"{api_base}/health")

    with httpx.Client(timeout=TIMEOUT) as client:
        # Schritt 1: Login
        login_response = client.post(
            f"{auth_base}/login",
            json={"username": "admin", "password": "changeme"},
        )

        if login_response.status_code == 401:
            pytest.skip(
                "Default-Credentials ungültig — "
                "nutze `make reset-default-password` um zurückzusetzen"
            )

        assert login_response.status_code == 200, (
            f"Login fehlgeschlagen: HTTP {login_response.status_code} — "
            f"{login_response.text[:300]}"
        )

        token_data = login_response.json()
        assert "access_token" in token_data, (
            f"Login-Response enthält keinen access_token: {token_data}"
        )
        token = token_data["access_token"]
        assert token_data.get("token_type", "").lower() == "bearer", (
            f"Unerwarteter token_type: {token_data.get('token_type')}"
        )

        # Schritt 2: /conversations mit Token
        conv_response = client.get(
            f"{api_base}/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert conv_response.status_code == 200, (
            f"GET /conversations fehlgeschlagen: HTTP {conv_response.status_code} — "
            f"{conv_response.text[:300]}"
        )

        conversations = conv_response.json()
        assert isinstance(conversations, list), (
            f"Erwarte Liste, bekam: {type(conversations)}"
        )


@pytest.mark.integration
def test_invalid_token_returns_401(api_base: str) -> None:
    """Ungültiger Token → 401 Unauthorized.

    Stellt sicher, dass der API-Service Token-Validierung korrekt durchführt
    und keine Daten bei ungültiger Authentifizierung preisgibt.
    """
    _skip_if_unreachable(f"{api_base}/health")

    invalid_token = "this.is.not.a.valid.jwt.token"

    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.get(
            f"{api_base}/conversations",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

    assert response.status_code == 401, (
        f"Erwarte 401 bei ungültigem Token, bekam: HTTP {response.status_code} — "
        f"{response.text[:300]}"
    )


@pytest.mark.integration
def test_create_and_list_conversation(
    auth_base: str, api_base: str, auth_token: str
) -> None:
    """Konversation erstellen, dann listen — End-to-End Datenbankfluss.

    Prüft:
    1. POST /conversations → 201 + Konversations-Objekt
    2. GET /conversations → Liste enthält die neue Konversation
    3. Teardown: Konversation ist in der Liste sichtbar (kein Cleanup nötig,
       da Testdaten in WORKSPACE-Zone und kein FAMILY_PRIVATE-Inhalt)
    """
    _skip_if_unreachable(f"{api_base}/health")

    headers = {"Authorization": f"Bearer {auth_token}"}
    test_title = "Integration-Test Konversation (automatisch erstellt)"

    with httpx.Client(timeout=TIMEOUT) as client:
        # Schritt 1: Konversation erstellen
        create_response = client.post(
            f"{api_base}/conversations",
            json={"title": test_title, "zone": "WORKSPACE"},
            headers=headers,
        )

        assert create_response.status_code == 201, (
            f"POST /conversations fehlgeschlagen: HTTP {create_response.status_code} — "
            f"{create_response.text[:300]}"
        )

        created = create_response.json()
        assert "id" in created, f"Konversation hat keine ID: {created}"
        assert created.get("title") == test_title, (
            f"Titel stimmt nicht überein: {created.get('title')!r} != {test_title!r}"
        )
        assert created.get("zone") == "WORKSPACE", (
            f"Zone stimmt nicht überein: {created.get('zone')!r}"
        )
        conversation_id = created["id"]

        # Schritt 2: Liste abrufen und neue Konversation finden
        list_response = client.get(
            f"{api_base}/conversations",
            headers=headers,
        )

        assert list_response.status_code == 200, (
            f"GET /conversations fehlgeschlagen: HTTP {list_response.status_code}"
        )

        conversations = list_response.json()
        ids = [c["id"] for c in conversations]
        assert conversation_id in ids, (
            f"Neu erstellte Konversation {conversation_id!r} nicht in Liste gefunden. "
            f"Vorhandene IDs: {ids[:5]}"
        )


@pytest.mark.integration
def test_health_chain(auth_base: str, api_base: str) -> None:
    """Auth + API + Embeddings alle healthy.

    Prüft die Health-Endpunkte der kritischen Services im Verbund.
    Embeddings (Port 8004) wird übersprungen wenn nicht erreichbar —
    Auth und API müssen jedoch beide antworten.
    """
    results: dict[str, int | str] = {}

    with httpx.Client(timeout=TIMEOUT) as client:
        # Auth — kritisch
        try:
            r = client.get(f"{auth_base}/health")
            results["auth"] = r.status_code
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            pytest.skip(f"Auth-Service nicht erreichbar: {exc}")

        # API — kritisch
        try:
            r = client.get(f"{api_base}/health")
            results["api"] = r.status_code
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as exc:
            pytest.skip(f"API-Service nicht erreichbar: {exc}")

        # Embeddings — optional
        try:
            r = client.get("http://localhost:8004/health")
            results["embeddings"] = r.status_code
        except (httpx.ConnectError, httpx.TimeoutException, OSError):
            results["embeddings"] = "nicht erreichbar (optional)"

    # Auth und API müssen < 500 antworten
    assert isinstance(results["auth"], int) and results["auth"] < 500, (
        f"Auth-Service antwortet mit Server-Fehler: {results['auth']}"
    )
    assert isinstance(results["api"], int) and results["api"] < 500, (
        f"API-Service antwortet mit Server-Fehler: {results['api']}"
    )

    # Embeddings: wenn erreichbar, dann auch < 500
    if isinstance(results["embeddings"], int):
        assert results["embeddings"] < 500, (
            f"Embeddings-Service antwortet mit Server-Fehler: {results['embeddings']}"
        )
