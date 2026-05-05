"""
Kirobi Authentication Service
Zone: WORKSPACE
Purpose: User authentication, session management, and zone-based access control
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGEME-in-production-use-strong-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:{os.getenv('POSTGRES_PASSWORD', 'changeme')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'kirobi')}"

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
    yield
    # Shutdown
    await db_pool.close()


# FastAPI app
app = FastAPI(
    title="Kirobi Authentication Service",
    description="Authentication and authorization service for Kirobi family members",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_user_by_username(username: str) -> Optional[UserInDB]:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, display_name, email, role, password_hash, avatar_url, bio, is_active, created_at FROM users WHERE username = $1",
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


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
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

        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

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
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_sessions (id, user_id, session_token, device_info, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            session_id,
            user_id,
            token,
            {},  # device_info placeholder
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
            details,
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
    """Register a new user (admin only in production)"""
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
            user_data.role
        )

        # Set default permissions
        if user_data.role == "admin":
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

    await log_audit_event(user_id, "register", "user", {"username": user_data.username}, request)

    user = await get_user_by_id(user_id)
    return user


@app.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user_id": current_user.id, "username": current_user.username}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
