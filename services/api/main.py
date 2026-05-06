"""
Kirobi Main API Service
Zone: WORKSPACE
Purpose: Main API for family interactions with Kirobi
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
import asyncpg
import httpx
from dotenv import load_dotenv
import aiofiles
from pathlib import Path

load_dotenv()

# Configuration
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:{os.getenv('POSTGRES_PASSWORD', 'changeme')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'kirobi')}"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


# Pydantic Models
class User(BaseModel):
    id: str
    username: str
    display_name: str
    role: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    zone: str = "FAMILY_PRIVATE"


class Conversation(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    zone: str
    created_at: datetime
    updated_at: datetime
    archived: bool


class MessageCreate(BaseModel):
    content: str
    attachments: Optional[List[str]] = []


class Message(BaseModel):
    id: str
    conversation_id: str
    user_id: Optional[str]
    role: str
    content: str
    model_used: Optional[str]
    tokens_used: Optional[int]
    attachments: List = []
    metadata: dict = {}
    created_at: datetime


class FileUploadResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: Optional[str]
    zone: str
    created_at: datetime


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
    title="Kirobi API Service",
    description="Main API service for Kirobi family interactions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# `allow_origins=["*"]` together with `allow_credentials=True` is invalid per
# the CORS spec — browsers reject the preflight. We mirror the auth service
# logic and resolve a concrete origin list from KIROBI_PUBLIC_ORIGINS, falling
# back to a regex that covers localhost, *.local and RFC1918 LAN addresses.
def _cors_kwargs() -> dict:
    raw = os.getenv("KIROBI_PUBLIC_ORIGINS", "").strip()
    if raw:
        origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        return {"allow_origins": origins}
    pattern = (
        r"^https?://("
        r"localhost(:\d+)?|127\.0\.0\.1(:\d+)?|"
        r"[a-zA-Z0-9-]+\.local(:\d+)?|"
        r"10\.\d+\.\d+\.\d+(:\d+)?|"
        r"192\.168\.\d+\.\d+(:\d+)?|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?"
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


# Dependency to get current user from auth service
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                return User(**user_data)
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}")


async def check_zone_permission(user_id: str, zone: str, permission_type: str = "read") -> bool:
    """Check if user has permission for a specific zone"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            f"SELECT can_{permission_type} FROM zone_permissions WHERE user_id = $1 AND zone = $2",
            user_id,
            zone
        )
        return result and result[f"can_{permission_type}"]


async def call_ollama(prompt: str, model: str = "llama3.1:8b", system_prompt: Optional[str] = None) -> str:
    """Call Ollama for LLM response"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                return f"Error calling Ollama: {response.status_code}"
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "service": "api"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/conversations", response_model=List[Conversation])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    archived: bool = False
):
    """List all conversations for current user"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, title, zone, created_at, updated_at, archived
            FROM conversations
            WHERE user_id = $1 AND archived = $2
            ORDER BY updated_at DESC
            """,
            current_user.id,
            archived
        )
        return [Conversation(**dict(row)) for row in rows]


@app.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    # Check zone permission
    if not await check_zone_permission(current_user.id, conversation_data.zone, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No write permission for zone {conversation_data.zone}"
        )

    conversation_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO conversations (id, user_id, title, zone)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id,
            current_user.id,
            conversation_data.title,
            conversation_data.zone
        )

        row = await conn.fetchrow(
            "SELECT id, user_id, title, zone, created_at, updated_at, archived FROM conversations WHERE id = $1",
            conversation_id
        )
        return Conversation(**dict(row))


@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, user_id, title, zone, created_at, updated_at, archived
            FROM conversations
            WHERE id = $1 AND user_id = $2
            """,
            conversation_id,
            current_user.id
        )

        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return Conversation(**dict(row))


@app.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def list_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """List messages in a conversation"""
    # Verify conversation ownership
    conversation = await get_conversation(conversation_id, current_user)

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, conversation_id, user_id, role, content, model_used, tokens_used, attachments, metadata, created_at
            FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            conversation_id,
            limit
        )
        return [Message(**dict(row)) for row in rows]


@app.post("/conversations/{conversation_id}/messages", response_model=Message)
async def create_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a message in a conversation and get AI response"""
    # Verify conversation ownership
    conversation = await get_conversation(conversation_id, current_user)

    # Save user message
    message_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO messages (id, conversation_id, user_id, role, content, attachments)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            message_id,
            conversation_id,
            current_user.id,
            "user",
            message_data.content,
            message_data.attachments
        )

        # Get conversation history for context
        history = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT 20
            """,
            conversation_id
        )

    # Load user profile for personalized response
    profile_path = f"/canon/family/{current_user.username}-profile.md"
    system_prompt = f"""Du bist Kirobi, ein persönlicher KI-Assistent für die Familie Darusi.

Du sprichst mit: {current_user.display_name} ({current_user.username})
Zone: {conversation.zone}

Sei persönlich, hilfsbereit und respektiere die Privatsphäre der Familie.
Antworte auf Deutsch und passe deinen Tonfall an den Nutzer an."""

    # Call Ollama for response
    model = "llama3.1:8b"
    if current_user.role == "admin":
        model = "llama3.1:70b"

    ai_response = await call_ollama(message_data.content, model=model, system_prompt=system_prompt)

    # Save AI response
    ai_message_id = str(uuid.uuid4())
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, model_used)
            VALUES ($1, $2, $3, $4, $5)
            """,
            ai_message_id,
            conversation_id,
            "assistant",
            ai_response,
            model
        )

        # Update conversation timestamp
        await conn.execute(
            "UPDATE conversations SET updated_at = NOW() WHERE id = $1",
            conversation_id
        )

        # Return AI message
        row = await conn.fetchrow(
            """
            SELECT id, conversation_id, user_id, role, content, model_used, tokens_used, attachments, metadata, created_at
            FROM messages WHERE id = $1
            """,
            ai_message_id
        )
        return Message(**dict(row))


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    zone: str = Form("FAMILY_PRIVATE"),
    current_user: User = Depends(get_current_user)
):
    """Upload a file (image, document, etc.)"""
    # Check zone permission
    if not await check_zone_permission(current_user.id, zone, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No write permission for zone {zone}"
        )

    # Create user-specific upload directory
    user_upload_dir = UPLOAD_DIR / current_user.username / zone.lower()
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = user_upload_dir / unique_filename

    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        file_size = len(content)

        # Save to database
        file_id = str(uuid.uuid4())
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO file_uploads (id, user_id, filename, original_filename, file_path, file_size, mime_type, zone)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                file_id,
                current_user.id,
                unique_filename,
                file.filename,
                str(file_path),
                file_size,
                file.content_type,
                zone
            )

            row = await conn.fetchrow(
                "SELECT id, filename, file_path, file_size, mime_type, zone, created_at FROM file_uploads WHERE id = $1",
                file_id
            )

        return FileUploadResponse(**dict(row))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.get("/uploads", response_model=List[FileUploadResponse])
async def list_uploads(
    zone: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List uploaded files for current user"""
    async with db_pool.acquire() as conn:
        if zone:
            rows = await conn.fetch(
                """
                SELECT id, filename, file_path, file_size, mime_type, zone, created_at
                FROM file_uploads
                WHERE user_id = $1 AND zone = $2
                ORDER BY created_at DESC
                """,
                current_user.id,
                zone
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, filename, file_path, file_size, mime_type, zone, created_at
                FROM file_uploads
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                current_user.id
            )

        return [FileUploadResponse(**dict(row)) for row in rows]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
