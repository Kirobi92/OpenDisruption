from __future__ import annotations

"""
Kirobi Ingest Service
Zone: WORKSPACE
Purpose: Ingestion of text documents and files into the Kirobi knowledge base.
         Extracts text, validates zones, stores jobs in PostgreSQL, and forwards
         embeddings to the embeddings service.
"""

import io
import os
import uuid
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import asyncio

import aiofiles
import asyncpg
import httpx
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

try:
    from kirobi_core.analytics_client import track as _analytics_track
except Exception:  # noqa: BLE001
    async def _analytics_track(*_args, **_kwargs) -> None:  # type: ignore[misc]
        pass
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_INTERNAL_SERVICE_PORTS = {
    "auth": 8000,
    "embeddings": 8000,
}


def _service_url(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    target_port = _INTERNAL_SERVICE_PORTS.get(host)
    if not target_port or parsed.port in (None, target_port):
        return value.rstrip("/")
    netloc = f"{host}:{target_port}"
    return urlunparse(parsed._replace(netloc=netloc)).rstrip("/")


DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'changeme')}@"
    f"{os.getenv('POSTGRES_HOST', 'postgres')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'kirobi')}"
)
AUTH_SERVICE_URL = _service_url(os.getenv("AUTH_SERVICE_URL", "http://auth:8000"))
EMBEDDINGS_SERVICE_URL = _service_url(os.getenv("EMBEDDINGS_SERVICE_URL", "http://embeddings:8004"))
INGEST_DIR = Path(os.getenv("INGEST_DIR", "/data/ingest"))
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024

KNOWN_ZONES = {"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"}
AUTONOMOUS_INGEST_ZONES = {"PUBLIC", "WORKSPACE"}
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/octet-stream",  # fallback for .md uploads
}
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ingest")

# ---------------------------------------------------------------------------
# Optional PDF extraction
# ---------------------------------------------------------------------------

try:
    import pdfplumber  # type: ignore

    _PDF_BACKEND = "pdfplumber"
except ImportError:
    try:
        import PyPDF2  # type: ignore

        _PDF_BACKEND = "pypdf2"
    except ImportError:
        _PDF_BACKEND = None

logger.info("PDF backend: %s", _PDF_BACKEND or "none (PDF ingestion disabled)")

# ---------------------------------------------------------------------------
# Database schema
# ---------------------------------------------------------------------------

INGEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS ingest_jobs (
    id              TEXT PRIMARY KEY,
    status          TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    zone            TEXT NOT NULL,
    source_path     TEXT,
    source_type     TEXT NOT NULL DEFAULT 'text',
    error           TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ingest_jobs_status_idx ON ingest_jobs(status);
CREATE INDEX IF NOT EXISTS ingest_jobs_zone_idx   ON ingest_jobs(zone);
CREATE INDEX IF NOT EXISTS ingest_jobs_created_idx ON ingest_jobs(created_at DESC);
"""

# ---------------------------------------------------------------------------
# Database pool
# ---------------------------------------------------------------------------

db_pool: Optional[asyncpg.Pool] = None


async def _ensure_schema() -> None:
    """Create ingest_jobs table idempotently on startup."""
    async with db_pool.acquire() as conn:
        await conn.execute(INGEST_SCHEMA)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        INGEST_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.warning("Cannot create INGEST_DIR=%s (permission denied) — skipping.", INGEST_DIR)
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        await _ensure_schema()
    logger.info("Ingest service started. INGEST_DIR=%s", INGEST_DIR)
    yield
    if db_pool is not None:
        await db_pool.close()
    logger.info("Ingest service stopped.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Kirobi Ingest Service",
    description="Ingestion of text and files into the Kirobi knowledge base.",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — mirrors api/auth service pattern (no wildcard with credentials)
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


app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["X-Request-Id"],
    max_age=3600,
)

# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/token")


class UserInfo(BaseModel):
    id: str
    username: str
    role: str


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    """Validate JWT token against the auth service."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{AUTH_SERVICE_URL}/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.RequestError as exc:
            logger.error("Auth service unreachable: %s", type(exc).__name__)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )
        if resp.status_code == 200:
            data = resp.json()
            return UserInfo(
                id=data.get("id", ""),
                username=data.get("username", ""),
                role=data.get("role", ""),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TextIngestRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text content to ingest")
    zone: str = Field(..., description="Zone classification (e.g. WORKSPACE)")
    title: Optional[str] = Field(None, max_length=500)
    source: Optional[str] = Field(None, max_length=500, description="Origin URL or path")
    human_approved: bool = Field(
        default=False,
        description="Explicit human approval required for FAMILY_PRIVATE ingest",
    )
    approval_note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason / confirmation note for protected-zone ingest",
    )
    metadata: dict = Field(default_factory=dict)


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    zone: str
    source_path: Optional[str]
    source_type: str
    error: Optional[str]
    metadata: dict
    created_at: datetime
    completed_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truthy_form_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _zone_ingest_metadata(
    zone: str,
    *,
    human_approved: bool = False,
    approval_note: Optional[str] = None,
) -> dict:
    if zone not in KNOWN_ZONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid zone '{zone}'. Known zones: {sorted(KNOWN_ZONES)}",
        )
    clean_note = (approval_note or "").strip() or None
    metadata = {
        "zone_policy": zone,
        "storage_mode": "local-first-file-backed",
        "local_only": True,
        "approval_required": zone == "FAMILY_PRIVATE",
        "human_approved": False,
        "approval_note": clean_note,
        "refusal_semantics": "zone-aware",
    }
    if zone in AUTONOMOUS_INGEST_ZONES:
        return metadata
    if zone == "FAMILY_PRIVATE":
        if not human_approved or not clean_note:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "FAMILY_PRIVATE ingest requires explicit local human approval "
                    "and a non-empty approval_note."
                ),
            )
        metadata["human_approved"] = True
        metadata["refusal_semantics"] = "family-private-requires-human-approval"
        return metadata
    if zone == "QUARANTINE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="QUARANTINE content must be reviewed before it can be ingested or embedded.",
        )
    if zone == "SACRED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SACRED ingest is refused by this service.",
        )
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Ingest is not allowed for zone '{zone}'.")


def _validate_zone(zone: str) -> None:
    """Compatibility wrapper for autonomous ingest contract tests."""
    _zone_ingest_metadata(zone)


async def _create_job(
    job_id: str,
    zone: str,
    source_type: str,
    source_path: Optional[str],
    metadata: dict,
) -> None:
    import json as _json

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO ingest_jobs (id, status, zone, source_type, source_path, metadata)
            VALUES ($1, 'pending', $2, $3, $4, $5::jsonb)
            """,
            job_id,
            zone,
            source_type,
            source_path,
            _json.dumps(metadata),
        )


async def _update_job(
    job_id: str,
    new_status: str,
    error: Optional[str] = None,
) -> None:
    completed_at = datetime.now(timezone.utc) if new_status in ("completed", "failed") else None
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE ingest_jobs
            SET status = $2, error = $3, completed_at = $4
            WHERE id = $1
            """,
            job_id,
            new_status,
            error,
            completed_at,
        )


async def _send_to_embeddings(
    job_id: str,
    text: str,
    zone: str,
    metadata: dict,
) -> None:
    """Forward extracted text to the embeddings service for vector storage."""
    payload = {
        "doc_id": job_id,
        "text": text,
        "zone": zone,
        "doc_type": "document",
        "metadata": metadata,
        "family_private_approved": bool(metadata.get("human_approved")),
        "approval_note": metadata.get("approval_note"),
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{EMBEDDINGS_SERVICE_URL}/store",
            json=payload,
        )
        resp.raise_for_status()


def _extract_text_from_pdf(raw: bytes) -> str:
    """Extract plain text from PDF bytes using the best available backend."""
    if _PDF_BACKEND == "pdfplumber":
        import pdfplumber  # type: ignore

        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages).strip()

    if _PDF_BACKEND == "pypdf2":
        import PyPDF2  # type: ignore

        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="PDF ingestion is not available: no PDF library installed (pdfplumber or PyPDF2).",
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Health check — verifies DB connectivity."""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "ingest",
        "db": "ok" if db_ok else "error",
        "pdf_backend": _PDF_BACKEND or "none",
    }


@app.post(
    "/ingest/text",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=IngestJobResponse,
    tags=["ingest"],
)
async def ingest_text(
    request: TextIngestRequest,
    current_user: UserInfo = Depends(get_current_user),
) -> IngestJobResponse:
    """
    Ingest a plain-text document.

    The text is stored on disk under INGEST_DIR and forwarded to the
    embeddings service asynchronously.  A job record is created in
    PostgreSQL so callers can poll /ingest/status/{job_id}.
    """
    zone_meta = _zone_ingest_metadata(
        request.zone,
        human_approved=request.human_approved,
        approval_note=request.approval_note,
    )

    job_id = str(uuid.uuid4())
    meta = {
        **request.metadata,
        **zone_meta,
        "title": request.title,
        "source": request.source,
        "user_id": current_user.id,
        "username": current_user.username,
    }

    # Persist text to filesystem (system of record)
    dest = INGEST_DIR / request.zone.lower() / current_user.username / f"{job_id}.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(dest, "w", encoding="utf-8") as fh:
        await fh.write(request.text)

    await _create_job(job_id, request.zone, "text", str(dest), meta)
    await _update_job(job_id, "processing")

    try:
        await _send_to_embeddings(job_id, request.text, request.zone, meta)
        await _update_job(job_id, "completed")
        asyncio.create_task(_analytics_track("ingest", zone=request.zone, metadata={"source": "text", "job_id": job_id}))
        logger.info("Text ingest completed. job_id=%s zone=%s", job_id, request.zone)
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {exc}"
        logger.error("Text ingest failed. job_id=%s error=%s", job_id, err_msg)
        await _update_job(job_id, "failed", error=err_msg)

    return await _get_job_or_404(job_id)


@app.post(
    "/ingest/file",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=IngestJobResponse,
    tags=["ingest"],
)
async def ingest_file(
    file: UploadFile = File(...),
    zone: str = Form(...),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    human_approved: Optional[str] = Form(None),
    approval_note: Optional[str] = Form(None),
    current_user: UserInfo = Depends(get_current_user),
) -> IngestJobResponse:
    """
    Ingest a file (PDF, TXT, MD).

    The file is saved to INGEST_DIR, text is extracted, and forwarded to
    the embeddings service.
    """
    zone_meta = _zone_ingest_metadata(
        zone,
        human_approved=_truthy_form_value(human_approved),
        approval_note=approval_note,
    )

    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
        )

    job_id = str(uuid.uuid4())
    safe_name = f"{job_id}{suffix}"
    dest = INGEST_DIR / zone.lower() / current_user.username / safe_name
    dest.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(dest, "wb") as fh:
        await fh.write(raw)

    meta = {
        **zone_meta,
        "original_filename": file.filename,
        "file_size": len(raw),
        "title": title,
        "source": source,
        "user_id": current_user.id,
        "username": current_user.username,
    }

    await _create_job(job_id, zone, suffix.lstrip("."), str(dest), meta)
    await _update_job(job_id, "processing")

    # Extract text
    try:
        if suffix == ".pdf":
            text = _extract_text_from_pdf(raw)
        else:
            text = raw.decode("utf-8", errors="replace")
    except HTTPException:
        raise
    except Exception as exc:
        err_msg = f"Text extraction failed: {type(exc).__name__}: {exc}"
        logger.error("File ingest extraction error. job_id=%s error=%s", job_id, err_msg)
        await _update_job(job_id, "failed", error=err_msg)
        return await _get_job_or_404(job_id)

    if not text.strip():
        await _update_job(job_id, "failed", error="Extracted text is empty.")
        return await _get_job_or_404(job_id)

    try:
        await _send_to_embeddings(job_id, text, zone, meta)
        await _update_job(job_id, "completed")
        asyncio.create_task(_analytics_track("ingest", zone=zone, metadata={"source": suffix.lstrip("."), "job_id": job_id}))
        logger.info(
            "File ingest completed. job_id=%s zone=%s file=%s",
            job_id,
            zone,
            file.filename,
        )
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {exc}"
        logger.error("File ingest embedding error. job_id=%s error=%s", job_id, err_msg)
        await _update_job(job_id, "failed", error=err_msg)

    return await _get_job_or_404(job_id)


@app.get(
    "/ingest/status/{job_id}",
    response_model=IngestJobResponse,
    tags=["ingest"],
)
async def get_ingest_status(
    job_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> IngestJobResponse:
    """Return the current status of an ingest job."""
    return await _get_job_or_404(job_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_job_or_404(job_id: str) -> IngestJobResponse:
    import json as _json

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, status, zone, source_path, source_type,
                   error, metadata, created_at, completed_at
            FROM ingest_jobs
            WHERE id = $1
            """,
            job_id,
        )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingest job '{job_id}' not found.",
        )
    meta = row["metadata"]
    if isinstance(meta, str):
        meta = _json.loads(meta)
    return IngestJobResponse(
        job_id=row["id"],
        status=row["status"],
        zone=row["zone"],
        source_path=row["source_path"],
        source_type=row["source_type"],
        error=row["error"],
        metadata=meta,
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )
