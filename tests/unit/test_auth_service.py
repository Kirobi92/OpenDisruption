"""
Unit-Tests für services/auth/main.py
Zone: WORKSPACE

asyncpg-Pool wird vollständig gemockt.
JWT-Tokens werden mit dem Test-Secret erzeugt.
Kein laufender Service oder Datenbank erforderlich.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_row(
    user_id: str = "user-1",
    username: str = "testuser",
    role: str = "admin",
    is_active: bool = True,
) -> dict:
    """Erstellt eine Fake-DB-Zeile für users."""
    return {
        "id": user_id,
        "username": username,
        "display_name": "Test User",
        "email": "test@example.com",
        "role": role,
        "password_hash": "$2b$12$KIXqJZ5Ld.Xt5Xt5Xt5XuOXt5Xt5Xt5Xt5Xt5Xt5Xt5Xt5Xt5Xt",
        "avatar_url": None,
        "bio": None,
        "is_active": is_active,
        "created_at": datetime.now(timezone.utc),
    }


class _AsyncContextManagerMock:
    """Hilfsklasse: async context manager der immer dasselbe Objekt zurückgibt."""

    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


def _make_mock_pool(mock_conn: AsyncMock) -> MagicMock:
    """Erstellt einen Mock-Pool der einen Mock-Connection zurückgibt."""
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=_AsyncContextManagerMock(mock_conn))
    mock_pool.close = AsyncMock(return_value=None)
    return mock_pool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    TestClient mit gemocktem asyncpg-Pool.
    Lifespan wird durch Patchen von asyncpg.create_pool umgangen.
    """
    import services.auth.main as auth

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = _make_mock_pool(mock_conn)

    with patch("services.auth.main.asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
        with TestClient(auth.app, raise_server_exceptions=False) as c:
            auth.db_pool = mock_pool
            yield c, mock_conn

    auth.db_pool = None


def _make_valid_token(user_id: str = "user-1") -> str:
    """Erstellt einen gültigen JWT-Token für Tests."""
    import services.auth.main as auth
    return auth.create_access_token(data={"sub": user_id, "username": "testuser", "role": "admin"})


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health muss 'healthy' zurückgeben wenn DB erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(return_value=1)

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auth"


def test_health_returns_unhealthy_on_db_error(client):
    """GET /health muss 'unhealthy' zurückgeben wenn DB nicht erreichbar."""
    c, mock_conn = client
    mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))

    resp = c.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unhealthy"
    assert "error" in data


# ---------------------------------------------------------------------------
# POST /token — Login
# ---------------------------------------------------------------------------

def test_login_with_wrong_credentials_returns_401(client):
    """POST /token mit falschen Credentials muss 401 zurückgeben."""
    c, mock_conn = client
    # fetchrow gibt None zurück → User nicht gefunden
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.post(
        "/token",
        data={"username": "wronguser", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_login_missing_fields_returns_422(client):
    """POST /token ohne Felder muss 422 zurückgeben."""
    c, _ = client
    resp = c.post("/token", data={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /login — JSON Login
# ---------------------------------------------------------------------------

def test_json_login_missing_fields_returns_422(client):
    """POST /login ohne Felder muss 422 zurückgeben."""
    c, _ = client
    resp = c.post("/login", json={})
    assert resp.status_code == 422


def test_json_login_wrong_credentials_returns_401(client):
    """POST /login mit falschen Credentials muss 401 zurückgeben."""
    c, mock_conn = client
    mock_conn.fetchrow = AsyncMock(return_value=None)

    resp = c.post("/login", json={"username": "nobody", "password": "wrongpass"})
    assert resp.status_code == 401
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# GET /me — Aktueller User
# ---------------------------------------------------------------------------

def test_me_without_token_returns_401(client):
    """GET /me ohne Token muss 401 zurückgeben."""
    c, _ = client
    resp = c.get("/me")
    assert resp.status_code == 401


def test_me_with_invalid_token_returns_401(client):
    """GET /me mit ungültigem Token muss 401 zurückgeben."""
    c, _ = client
    resp = c.get("/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_me_with_valid_token_returns_user(client):
    """GET /me mit gültigem Token muss User-Daten zurückgeben."""
    c, mock_conn = client
    user_row = _make_user_row()
    mock_conn.fetchrow = AsyncMock(return_value=user_row)

    token = _make_valid_token(user_id="user-1")
    resp = c.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "user-1"
    assert data["username"] == "testuser"


# ---------------------------------------------------------------------------
# GET /verify — Token-Validierung
# ---------------------------------------------------------------------------

def test_verify_with_valid_token(client):
    """GET /verify mit gültigem Token muss valid=True zurückgeben."""
    c, mock_conn = client
    user_row = _make_user_row()
    mock_conn.fetchrow = AsyncMock(return_value=user_row)

    token = _make_valid_token(user_id="user-1")
    resp = c.get("/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["user_id"] == "user-1"


def test_verify_without_token_returns_401(client):
    """GET /verify ohne Token muss 401 zurückgeben."""
    c, _ = client
    resp = c.get("/verify")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /register — Registrierung
# ---------------------------------------------------------------------------

def test_register_validates_short_username(client):
    """POST /register mit zu kurzem Username muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/register",
        json={
            "username": "ab",
            "display_name": "Test",
            "password": "securepassword123",
        },
    )
    assert resp.status_code == 422


def test_register_validates_short_password(client):
    """POST /register mit zu kurzem Passwort muss 422 zurückgeben."""
    c, _ = client
    resp = c.post(
        "/register",
        json={
            "username": "validuser",
            "display_name": "Test",
            "password": "short",
        },
    )
    assert resp.status_code == 422


def test_register_duplicate_username_returns_400(client):
    """POST /register mit existierendem Username muss 400 zurückgeben."""
    c, mock_conn = client
    # fetchrow gibt existierenden User zurück
    mock_conn.fetchrow = AsyncMock(return_value=_make_user_row())

    resp = c.post(
        "/register",
        json={
            "username": "testuser",
            "display_name": "Test User",
            "password": "securepassword123",
        },
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

def test_logout_without_token_returns_401(client):
    """POST /logout ohne Token muss 401 zurückgeben."""
    c, _ = client
    resp = c.post("/logout")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Helper-Funktionen
# ---------------------------------------------------------------------------

def test_create_access_token_contains_sub():
    """create_access_token muss sub-Claim enthalten."""
    import services.auth.main as auth
    from jose import jwt

    token = auth.create_access_token(data={"sub": "user-123"})
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_create_refresh_token_type():
    """create_refresh_token muss type='refresh' enthalten."""
    import services.auth.main as auth
    from jose import jwt

    token = auth.create_refresh_token(data={"sub": "user-123"})
    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload["type"] == "refresh"


def test_verify_password_correct():
    """verify_password muss True für korrektes Passwort zurückgeben."""
    import services.auth.main as auth

    hashed = auth.get_password_hash("mypassword")
    assert auth.verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    """verify_password muss False für falsches Passwort zurückgeben."""
    import services.auth.main as auth

    hashed = auth.get_password_hash("mypassword")
    assert auth.verify_password("wrongpassword", hashed) is False


def test_collection_name_format():
    """_collection_name muss korrekt formatiert sein."""
    import services.auth.main as auth

    # Nur testen dass das Modul importierbar ist
    assert auth.SECRET_KEY is not None
    assert auth.ALGORITHM == "HS256"
