"""
Kirobi Video Generation Service
Zone: WORKSPACE
Purpose: KI-Videogenerierung via Ollama (Text-to-Video-Prompts)
Port: 8014
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)
VIDEO_STORAGE_PATH = Path(os.getenv("VIDEO_STORAGE_PATH", "/data/videos"))
try:
    VIDEO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
except PermissionError:
    pass  # Im Container wird das Volume gemountet; außerhalb ignorieren

# ---------------------------------------------------------------------------
# DB schema
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS video_jobs (
    id               TEXT PRIMARY KEY,
    prompt           TEXT NOT NULL,
    resolution       TEXT,
    duration_seconds INT,
    zone             TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    file_path        TEXT,
    error            TEXT,
    metadata         JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    completed_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS video_jobs_status_idx ON video_jobs(status);
CREATE INDEX IF NOT EXISTS video_jobs_created_idx ON video_jobs(created_at DESC);
"""

# ---------------------------------------------------------------------------
# Available resolutions
# ---------------------------------------------------------------------------
AVAILABLE_RESOLUTIONS = [
    {"id": "480p", "name": "480p", "width": 854, "height": 480, "description": "Standard Definition"},
    {"id": "720p", "name": "720p HD", "width": 1280, "height": 720, "description": "High Definition"},
    {"id": "1080p", "name": "1080p Full HD", "width": 1920, "height": 1080, "description": "Full High Definition"},
    {"id": "1440p", "name": "1440p QHD", "width": 2560, "height": 1440, "description": "Quad High Definition"},
    {"id": "4k", "name": "4K UHD", "width": 3840, "height": 2160, "description": "Ultra High Definition"},
    {"id": "square", "name": "Square (1:1)", "width": 1080, "height": 1080, "description": "Quadratisch für Social Media"},
    {"id": "portrait", "name": "Portrait (9:16)", "width": 1080, "height": 1920, "description": "Hochformat für Mobile/Stories"},
]

# ---------------------------------------------------------------------------
# DB pool
# ---------------------------------------------------------------------------
db_pool: Optional[asyncpg.Pool] = None


async def _ensure_schema() -> None:
    """Idempotent table bootstrap on first start."""
    async with db_pool.acquire() as conn:
        await conn.execute(_SCHEMA)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Text-to-Video-Prompt")
    duration: int = Field(10, ge=1, le=300, description="Dauer in Sekunden")
    zone: str = Field("WORKSPACE", description="Sicherheitszone")
    resolution: str = Field("720p", description="Videoauflösung")


class JobResponse(BaseModel):
    job_id: str
    status: str
    prompt: str
    resolution: str
    duration_seconds: int
    zone: str
    file_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# CORS helper
# ---------------------------------------------------------------------------
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
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+(:\d+)?|"
        r"100\.(6[4-9]|[7-9]\d|1[0-1]\d|12[0-7])\.\d+\.\d+(:\d+)?"
        r")$"
    )
    return {"allow_origin_regex": pattern}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    await _ensure_schema()
    yield
    await db_pool.close()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Kirobi Video Generation Service",
    description="KI-Videogenerierung via Ollama — Zone: WORKSPACE",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-User-Id"],
    max_age=3600,
)


# ---------------------------------------------------------------------------
# Helper: Ollama erreichbar?
# ---------------------------------------------------------------------------
async def _check_ollama() -> dict:
    """Prüft ob Ollama erreichbar ist und gibt verfügbare Modelle zurück."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {"reachable": True, "models": models}
            return {"reachable": False, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"reachable": False, "error": str(exc)}


def _row_to_job_response(row: dict) -> JobResponse:
    """Konvertiert eine DB-Zeile in ein JobResponse-Objekt."""
    data = dict(row)
    raw_meta = data.get("metadata")
    if isinstance(raw_meta, str):
        try:
            data["metadata"] = json.loads(raw_meta)
        except json.JSONDecodeError:
            data["metadata"] = {}
    elif raw_meta is None:
        data["metadata"] = {}
    return JobResponse(
        job_id=data["id"],
        status=data["status"],
        prompt=data["prompt"],
        resolution=data.get("resolution") or "720p",
        duration_seconds=data.get("duration_seconds") or 10,
        zone=data["zone"],
        file_path=data.get("file_path"),
        error=data.get("error"),
        created_at=data["created_at"],
        completed_at=data.get("completed_at"),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health-Check: prüft DB und Ollama-Erreichbarkeit."""
    db_ok = False
    db_error: Optional[str] = None
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception as exc:
        db_error = str(exc)

    ollama_status = await _check_ollama()

    overall = "healthy" if db_ok and ollama_status["reachable"] else "degraded"
    return {
        "status": overall,
        "service": "video-generation",
        "port": 8014,
        "database": {"ok": db_ok, "error": db_error},
        "ollama": ollama_status,
    }


@app.post("/generate", response_model=JobCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(req: GenerateRequest):
    """
    Erstellt einen asynchronen Video-Generierungs-Job.
    Die eigentliche Generierung erfolgt im Hintergrund.
    """
    job_id = str(uuid.uuid4())

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO video_jobs
                (id, prompt, resolution, duration_seconds, zone, status, metadata)
            VALUES ($1, $2, $3, $4, $5, 'pending', $6)
            """,
            job_id,
            req.prompt,
            req.resolution,
            req.duration,
            req.zone,
            json.dumps({"ollama_host": OLLAMA_HOST}),
        )

    return JobCreatedResponse(
        job_id=job_id,
        status="pending",
        message=f"Video-Generierungs-Job '{job_id}' wurde erstellt und wird verarbeitet.",
    )


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Gibt den Status eines Video-Generierungs-Jobs zurück."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, prompt, resolution, duration_seconds, zone, status,
                   file_path, error, metadata, created_at, completed_at
            FROM video_jobs
            WHERE id = $1
            """,
            job_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' nicht gefunden")

    return _row_to_job_response(row)


@app.get("/jobs", response_model=List[JobResponse])
async def list_jobs(x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    """Listet alle Video-Generierungs-Jobs des Users."""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, prompt, resolution, duration_seconds, zone, status,
                   file_path, error, metadata, created_at, completed_at
            FROM video_jobs
            ORDER BY created_at DESC
            LIMIT 100
            """,
        )

    return [_row_to_job_response(row) for row in rows]


@app.get("/resolutions")
async def list_resolutions():
    """Gibt verfügbare Videoauflösungen zurück."""
    return {"resolutions": AVAILABLE_RESOLUTIONS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
