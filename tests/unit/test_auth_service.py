"""
Unit-Tests für services/auth/main.py
Zone: WORKSPACE

Strategie:
- jose, passlib und asyncpg werden via sys.modules gemockt, bevor
  das Modul importiert wird (fehlende Service-Dependencies).
- asyncpg.create_pool wird durch AsyncMock ersetzt.
- TestClient als Context-Manager für korrekten lifespan.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Stub-Module für fehlende Service-Dependencies
# ---------------------------------------------------------------------------

def _install_stubs() -> None:
    """Installiert Stub-Module für jose und passlib, falls nicht vorhanden."""
    # jose
    if "jose" not in sys.modules:
        jose_mod = types.ModuleType("jose")
        jose_mod.JWTError = Exception

        jwt_mod = types.ModuleType("jose.jwt")

        def _encode(data, key, algorithm="HS256"):
            import json, base64
            return base64.b64encode(json.dumps(data).encode()).decode()

        def _decode(token, key, algorithms=None):
            import json, base64
            try:
                return json.loads(base64.b64decode(token.encode()).decode())
            except Exception:
                raise jose_mod.JWTError("invalid token")

        jwt_mod.encode = _encode
        jwt_mod.decode = _decode
        jose_mod.jwt = jwt_mod
        sys.modules["jose"] = jose_mod
        sys.modules["jose.jwt"] = jwt_mod

    # passlib
    if "passlib" not in sys.modules:
        passlib_mod = types.ModuleType("passlib")
        context_mod = types.ModuleType("passlib.context")

        class _CryptContext:
            def __init__(self, **kwargs):
                pass
            def verify(self, plain, hashed):
                return plain == hashed  # triviale Verifikation für Tests
            def hash(self, password):
                return password  # kein echtes Hashing in Tests

        context_mod.CryptContext = _CryptContext
        passlib_mod.context = context_mod
        sys.modules["passlib"] = passlib_mod
        sys.modules["passlib.context"] = context_mod


_install_stubs()


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Mock-Pool
# ---------------------------------------------------------------------------

def _make_mock_pool():
    """Erstellt einen asyncpg.Pool-Mock."""
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=1)
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])

    pool = MagicMock()
    pool.close = AsyncMock(return_value=None)

    acquire_ctx = MagicMock()
    acquire_ctx.__aenter__ = AsyncMock(return_value=conn)
    acquire_ctx.__aexit__ = AsyncMock(return_value=False)
    pool.acquire = MagicMock(return_value=acquire_ctx)

    return pool, conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def auth_app():
    """Importiert services.auth.main einmalig mit gemocktem asyncpg."""
    mock_pool, mock_conn = _make_mock_pool()

    with patch("asyncpg.create_pool", new=AsyncMock(return_value=mock_pool)):
        # Modul frisch laden (oder aus Cache holen)
        if "services.auth.main" in sys.modules:
            del sys.modules["services.auth.main"]
        if "services.auth" in sys.modules:
            del sys.modules["services.auth"]

        import services.auth.main as auth_main

        # Pool direkt setzen, damit Endpoints ohne lifespan funktionieren
        auth_main.db_pool = mock_pool
        yield auth_main, mock_pool, mock_conn


@pytest.fixture()
def auth_client(auth_app):
    """TestClient für den auth service."""
    from fastapi.testclient import TestClient
    auth_main, mock_pool, mock_conn = auth_app

    # Pool vor jedem Test zurücksetzen
    auth_main.db_pool = mock_pool

    # lifespan überspringen: TestClient ohne context manager
    client = TestClient(auth_main.app, raise_server_exceptions=False)
    yield client, auth_main, mock_pool, mock_conn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_endpoint(self, auth_client):
        """GET /health → 200"""
        client, auth_main, mock_pool, mock_conn = auth_client
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestReadyEndpoint:
    def test_ready_endpoint(self, auth_client):
        """GET /ready → 200, 404 oder 503 (kein /ready im auth service → 404)"""
        client, *_ = auth_client
        response = client.get("/ready")
        assert response.status_code in (200, 404, 503)


class TestLoginEndpoint:
    def test_login_missing_credentials(self, auth_client):
        """POST /token ohne Body → 422 Unprocessable Entity"""
        client, *_ = auth_client
        response = client.post("/token")
        assert response.status_code == 422

    def test_login_wrong_credentials(self, auth_client):
        """POST /token mit falschen Credentials → 401"""
        client, auth_main, mock_pool, mock_conn = auth_client
        # DB gibt keinen User zurück
        mock_conn.fetchrow = AsyncMock(return_value=None)
        auth_main.db_pool = mock_pool

        response = client.post(
            "/token",
            data={"username": "wrong_user", "password": "wrong_password"},
        )
        assert response.status_code == 401

    def test_login_empty_username(self, auth_client):
        """POST /token mit leerem Username → 422"""
        client, *_ = auth_client
        response = client.post("/token", data={"username": "", "password": "test"})
        assert response.status_code == 422


class TestRegisterEndpoint:
    def test_register_user_schema_missing_fields(self, auth_client):
        """POST /register ohne Pflichtfelder → 422"""
        client, *_ = auth_client
        response = client.post("/register", json={})
        assert response.status_code == 422

    def test_register_user_schema_short_username(self, auth_client):
        """POST /register mit zu kurzem Username (< 3 Zeichen) → 422"""
        client, *_ = auth_client
        response = client.post(
            "/register",
            json={
                "username": "ab",
                "display_name": "Test User",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

    def test_register_user_schema_short_password(self, auth_client):
        """POST /register mit zu kurzem Passwort (< 8 Zeichen) → 422"""
        client, *_ = auth_client
        response = client.post(
            "/register",
            json={
                "username": "validuser",
                "display_name": "Test User",
                "password": "short",
            },
        )
        assert response.status_code == 422


class TestProtectedEndpoints:
    def test_me_without_token(self, auth_client):
        """GET /me ohne Auth-Token → 401"""
        client, *_ = auth_client
        response = client.get("/me")
        assert response.status_code == 401

    def test_me_permissions_without_token(self, auth_client):
        """GET /me/permissions ohne Auth-Token → 401"""
        client, *_ = auth_client
        response = client.get("/me/permissions")
        assert response.status_code == 401

    def test_logout_without_token(self, auth_client):
        """POST /logout ohne Auth-Token → 401"""
        client, *_ = auth_client
        response = client.post("/logout")
        assert response.status_code == 401

    def test_verify_without_token(self, auth_client):
        """GET /verify ohne Auth-Token → 401"""
        client, *_ = auth_client
        response = client.get("/verify")
        assert response.status_code == 401
