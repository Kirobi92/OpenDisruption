from __future__ import annotations

"""
Kirobi Authentication Service
Zone: WORKSPACE
Purpose: User authentication, session management, and zone-based access control
"""

import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import bcrypt as _bcrypt
from pydantic import BaseModel, EmailStr, Field
import asyncpg
from dotenv import load_dotenv
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

load_dotenv()

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
if not SECRET_KEY or "CHANGEME" in SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY missing or too weak. "
        "Set a strong random string (>=32 chars, no 'CHANGEME') in .env."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

_PG_PW = os.environ.get("POSTGRES_PASSWORD", "")
if not _PG_PW or _PG_PW == "changeme":
    raise RuntimeError("POSTGRES_PASSWORD missing or insecure default ('changeme'). Set it in .env.")
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:{_PG_PW}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'kirobi')}"

# Security
# bcrypt direkt nutzen (passlib inkompatibel mit bcrypt >= 4.x)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


# Pydantic Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


class User(BaseModel):
    id: str
    username: str
    display_name: str
    email: Optional[EmailStr]
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class UserInDB(User):
    password_hash: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8)
    role: str = "family_member"


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ZonePermission(BaseModel):
    zone: str
    can_read: bool
    can_write: bool


class UserPermissions(BaseModel):
    user_id: str
    username: str
    zones: List[ZonePermission]


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    await _ensure_schema()
    await _ensure_default_user()
    await _ensure_family_users()
    yield
    # Shutdown
    await db_pool.close()


# Schema + first-run bootstrap ------------------------------------------------
USERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    display_name    TEXT NOT NULL,
    email           TEXT,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'family',
    avatar_url      TEXT,
    bio             TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS zone_permissions (
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    zone        TEXT NOT NULL,
    can_read    BOOLEAN NOT NULL DEFAULT FALSE,
    can_write   BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (user_id, zone)
);
CREATE TABLE IF NOT EXISTS user_sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token   TEXT UNIQUE NOT NULL,
    device_info     TEXT,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id     TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings    JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT,
    action          TEXT NOT NULL,
    resource_type   TEXT,
    details         JSONB,
    ip_address      TEXT,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS audit_log_user_idx     ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS user_sessions_user_idx ON user_sessions(user_id);
"""


async def _ensure_schema() -> None:
    """Create the auth tables if they don't exist yet (idempotent)."""
    async with db_pool.acquire() as conn:
        await conn.execute(USERS_SCHEMA)


async def _ensure_default_user() -> None:
    """Seed a default admin so the PWA's login screen works on first boot.

    Controlled by the env vars ``KIROBI_DEFAULT_USER`` and
    ``KIROBI_DEFAULT_PASSWORD``. Setting either to an empty string disables
    the bootstrap. Existing users are never modified.
    """
    username = os.getenv("KIROBI_DEFAULT_USER", "sven").strip()
    password = os.getenv("KIROBI_DEFAULT_PASSWORD", "").strip()
    if not username or not password:
        return
    display = os.getenv("KIROBI_DEFAULT_DISPLAY_NAME", username.title())
    role = os.getenv("KIROBI_DEFAULT_ROLE", "admin")
    async with db_pool.acquire() as conn:
        existing = await conn.fetchval("SELECT 1 FROM users WHERE username = $1", username)
        if existing:
            return
        user_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO users (id, username, display_name, password_hash, role)
            VALUES ($1, $2, $3, $4, $5)
            """,
            user_id,
            username,
            display,
            get_password_hash(password),
            role,
        )
        zones = [
            ("PUBLIC", True, True),
            ("WORKSPACE", True, True),
            ("FAMILY_PRIVATE", True, True),
            ("QUARANTINE", True, True),
            ("SACRED", True, True),
        ]
        for zone, r, w in zones:
            await conn.execute(
                "INSERT INTO zone_permissions (user_id, zone, can_read, can_write) "
                "VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                user_id, zone, r, w,
            )
        await conn.execute(
            "INSERT INTO user_preferences (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )


FAMILY_ZONES = [
    ("PUBLIC", True, True),
    ("WORKSPACE", True, False),
    ("FAMILY_PRIVATE", True, True),
]


async def _ensure_family_users() -> None:
    """Seed/refresh additional family users from ``KIROBI_FAMILY_USERS``.

    Format (comma-separated entries, fields ``:``-separated):
        username:password[:display_name[:role]]

    Existing usernames are kept but their password and zone permissions
    are reset to the configured defaults so families never get stuck on
    a forgotten password. Set ``KIROBI_FAMILY_USERS=`` to disable.
    """
    raw = os.getenv("KIROBI_FAMILY_USERS", "").strip()
    if not raw:
        return
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        username = parts[0].strip()
        password = parts[1].strip()
        display = parts[2].strip() if len(parts) > 2 and parts[2].strip() else username.title()
        role = parts[3].strip() if len(parts) > 3 and parts[3].strip() else "family_member"
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            pw_hash = get_password_hash(password)
            if row:
                user_id = row["id"]
                await conn.execute(
                    "UPDATE users SET password_hash = $1, display_name = $2, "
                    "role = $3, is_active = TRUE WHERE id = $4",
                    pw_hash, display, role, user_id,
                )
            else:
                user_id = str(uuid.uuid4())
                await conn.execute(
                    "INSERT INTO users (id, username, display_name, password_hash, role) "
                    "VALUES ($1, $2, $3, $4, $5)",
                    user_id, username, display, pw_hash, role,
                )
            for zone, can_r, can_w in FAMILY_ZONES:
                await conn.execute(
                    "INSERT INTO zone_permissions (user_id, zone, can_read, can_write) "
                    "VALUES ($1, $2, $3, $4) "
                    "ON CONFLICT (user_id, zone) DO UPDATE "
                    "SET can_read = EXCLUDED.can_read, can_write = EXCLUDED.can_write",
                    user_id, zone, can_r, can_w,
                )
            await conn.execute(
                "INSERT INTO user_preferences (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user_id,
            )


# FastAPI app
app = FastAPI(
    title="Kirobi Authentication Service",
    description="Authentication and authorization service for Kirobi family members",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# `allow_origins=["*"]` together with `allow_credentials=True` is invalid per
# the CORS spec — browsers reject the preflight. The PWA needs cookies/JWT
# headers so we resolve a concrete origin list from KIROBI_PUBLIC_ORIGINS
# (comma-separated). When the variable is empty we fall back to a regex that
# matches localhost, the *.local mDNS hostname, RFC1918 LAN addresses and
# Tailscale's CGNAT range (100.64.0.0/10) — enough for the family setup but
# never the literal "*".
def _cors_kwargs() -> dict:
    raw = os.getenv("KIROBI_PUBLIC_ORIGINS", "").strip()
    if raw:
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        return {"allow_origins": origins}
    # Fallback regex: localhost(:port), kirobi.local + any *.local + RFC1918
    # LAN addresses + Tailscale's 100.64.0.0/10 CGNAT range.
    pattern = (
        r"^https?://("
        r"localhost(:\d+)?|127\.0\.0\.1(:\d+)?|"
        r"[a-zA-Z0-9-]+\.local(:\d+)?|"
        r"10\.\d+\.\d+\.\d+(:\d+)?|"
        r"192\.168\.\d+\.\d+(:\d+)?|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?|"
        r"100\.(6[4-9]|[7-9]\d|1[0-1]\d|12[0-7])\.\d+\.\d+(:\d+)?"
        r")$"
    )
    return {"allow_origin_regex": pattern}


app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    max_age=3600,
)


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "jti": str(uuid.uuid4()),
        "type": "access",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_username(username: str) -> Optional[UserInDB]:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, display_name, email, role, password_hash, avatar_url, bio, is_active, created_at FROM users WHERE LOWER(username) = LOWER($1)",
            username
        )
        if row:
            return UserInDB(**dict(row))
    return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, display_name, email, role, avatar_url, bio, is_active, created_at FROM users WHERE id = $1",
            user_id
        )
        if row:
            return User(**dict(row))
    return None


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _decode_access_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        return TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    token_data = _decode_access_token(token)

    async with db_pool.acquire() as conn:
        active_session = await conn.fetchval(
            """
            SELECT 1 FROM user_sessions
            WHERE user_id = $1 AND session_token = $2 AND expires_at > NOW()
            """,
            token_data.user_id,
            token,
        )
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is no longer valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_user_permissions(user_id: str) -> List[ZonePermission]:
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT zone, can_read, can_write FROM zone_permissions WHERE user_id = $1",
            user_id
        )
        return [ZonePermission(**dict(row)) for row in rows]


async def create_session(user_id: str, token: str, request: Request) -> str:
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_sessions (id, user_id, session_token, device_info, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            session_id,
            user_id,
            token,
            json.dumps({}),
            request.client.host,
            request.headers.get("user-agent", ""),
            expires_at
        )

    return session_id


async def log_audit_event(user_id: str, action: str, resource_type: str, details: dict, request: Request):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO audit_log (user_id, action, resource_type, details, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            action,
            resource_type,
            json.dumps(details),
            request.client.host,
            request.headers.get("user-agent", "")
        )


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "auth"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    """Login endpoint - returns access and refresh tokens"""
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "username": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Create session
    await create_session(user.id, access_token, request)

    # Update last login
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_login = NOW() WHERE id = $1",
            user.id
        )

    # Audit log
    await log_audit_event(user.id, "login", "session", {"username": user.username}, request)

    return Token(access_token=access_token, refresh_token=refresh_token)


@app.post("/login", response_model=Token)
async def login_json(login_data: UserLogin, request: Request):
    """JSON-based login endpoint"""
    user = await authenticate_user(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": user.id, "username": user.username, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.id})

    await create_session(user.id, access_token, request)

    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user.id)

    await log_audit_event(user.id, "login", "session", {"username": user.username}, request)

    return Token(access_token=access_token, refresh_token=refresh_token)


@app.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@app.get("/me/permissions", response_model=UserPermissions)
async def read_user_permissions(current_user: User = Depends(get_current_user)):
    """Get current user's zone permissions"""
    permissions = await get_user_permissions(current_user.id)
    return UserPermissions(
        user_id=current_user.id,
        username=current_user.username,
        zones=permissions
    )


@app.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    token: str = Depends(oauth2_scheme),
    request: Request = None,
):
    """Rotate the current user's password and invalidate older sessions."""
    token_data = _decode_access_token(token)
    current_user = await get_user_by_id(token_data.user_id)
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_record = await get_user_by_username(current_user.username)
    if not user_record or not verify_password(password_data.current_password, user_record.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    new_hash = get_password_hash(password_data.new_password)
    async with db_pool.acquire() as conn:
        current_session = await conn.fetchval(
            "SELECT 1 FROM user_sessions WHERE user_id = $1 AND session_token = $2",
            current_user.id,
            token,
        )
        if not current_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current session is no longer valid",
            )
        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            new_hash,
            current_user.id,
        )
        await conn.execute(
            "DELETE FROM user_sessions WHERE user_id = $1 AND session_token <> $2",
            current_user.id,
            token,
        )

    await log_audit_event(current_user.id, "change_password", "user", {}, request)
    return {"message": "Password changed successfully"}


@app.post("/logout")
async def logout(current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme), request: Request = None):
    """Logout - invalidate session"""
    async with db_pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM user_sessions WHERE session_token = $1 AND user_id = $2",
            token,
            current_user.id
        )

    await log_audit_event(current_user.id, "logout", "session", {}, request)

    return {"message": "Successfully logged out"}


@app.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, request: Request):
    """Register a new user. Role 'admin' requires an existing admin session."""
    # Prevent unauthenticated privilege escalation: admin role requires auth header
    requested_role = user_data.role if user_data.role else "user"
    if requested_role == "admin":
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin role requires authentication",
            )
        try:
            token = auth_header.split(" ", 1)[1]
            token_data = _decode_access_token(token)
            caller = await get_user_by_id(token_data.user_id)
            if caller is None or caller.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins may create admin accounts",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins may create admin accounts",
            )
    else:
        requested_role = "user"

    # Check if user exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Hash password
    password_hash = get_password_hash(user_data.password)

    # Create user
    user_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, username, display_name, email, password_hash, role)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            user_data.username,
            user_data.display_name,
            user_data.email,
            password_hash,
            requested_role
        )

        # Set default permissions
        if requested_role == "admin":
            zones = [("PUBLIC", True, True), ("WORKSPACE", True, True), ("FAMILY_PRIVATE", True, True), ("QUARANTINE", True, True), ("SACRED", True, True)]
        else:
            zones = [("PUBLIC", True, True), ("WORKSPACE", True, False), ("FAMILY_PRIVATE", True, True)]

        for zone, can_read, can_write in zones:
            await conn.execute(
                """
                INSERT INTO zone_permissions (user_id, zone, can_read, can_write)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                zone,
                can_read,
                can_write
            )

        # Create default preferences
        await conn.execute(
            "INSERT INTO user_preferences (user_id) VALUES ($1)",
            user_id
        )

    await log_audit_event(user_id, "register", "user", {"username": user_data.username, "role": requested_role}, request)

    user = await get_user_by_id(user_id)
    return user


@app.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user_id": current_user.id, "username": current_user.username}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("BIND_HOST", "0.0.0.0"), port=8000)
