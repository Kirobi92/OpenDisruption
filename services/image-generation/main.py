"""
Kirobi Image Generation Service
Zone: WORKSPACE
Purpose: KI-Bildgenerierung via Ollama (llava/stable-diffusion)
Port: 8011
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
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
IMAGE_STORAGE_PATH = Path(os.getenv("IMAGE_STORAGE_PATH", "/data/images"))
IMAGE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# DB schema
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS generated_images (
    id          TEXT PRIMARY KEY,
    prompt      TEXT NOT NULL,
    model_used  TEXT,
    file_path   TEXT NOT NULL,
    zone        TEXT NOT NULL,
    width       INT,
    height      INT,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS generated_images_zone_idx
    ON generated_images(zone);
CREATE INDEX IF NOT EXISTS generated_images_created_idx
    ON generated_images(created_at DESC);
"""

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
    prompt: str = Field(..., min_length=1, description="Bildgenerierungs-Prompt")
    model: str = Field("llava:7b", description="Ollama-Modell")
    zone: str = Field("WORKSPACE", description="Sicherheitszone")
    width: int = Field(512, ge=64, le=2048, description="Bildbreite in Pixeln")
    height: int = Field(512, ge=64, le=2048, description="Bildhöhe in Pixeln")


class GeneratedImageResponse(BaseModel):
    id: str
    file_path: str
    zone: str
    model: str
    created_at: datetime


class ImageMetadata(BaseModel):
    id: str
    prompt: str
    model_used: Optional[str]
    file_path: str
    zone: str
    width: Optional[int]
    height: Optional[int]
    metadata: dict
    created_at: datetime


# ---------------------------------------------------------------------------
# CORS helper (mirrors services/api/main.py pattern)
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
    title="Kirobi Image Generation Service",
    description="KI-Bildgenerierung via Ollama — Zone: WORKSPACE",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    **_cors_kwargs(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
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


# ---------------------------------------------------------------------------
# Helper: Bild via Ollama generieren
# ---------------------------------------------------------------------------
async def _generate_via_ollama(prompt: str, model: str, width: int, height: int) -> bytes:
    """
    Ruft Ollama /api/generate auf.
    llava ist ein Vision-Modell — für echte Bildgenerierung wäre
    stable-diffusion nötig. Hier wird der Response-Text als PNG-Platzhalter
    gespeichert, falls kein Bild-Byte-Stream zurückkommt.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 256,
        },
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama returned HTTP {resp.status_code}: {resp.text[:200]}",
            )
        data = resp.json()

    # Wenn Ollama ein Bild-Byte-Array zurückgibt (z.B. stable-diffusion)
    images = data.get("images")
    if images and isinstance(images, list) and images[0]:
        import base64
        return base64.b64decode(images[0])

    # Fallback: minimales 1×1 PNG als Platzhalter + Metadaten-Kommentar
    # (llava generiert Text, kein Bild — wir speichern trotzdem eine Datei)
    response_text = data.get("response", "")
    return _make_placeholder_png(width, height, response_text)


def _make_placeholder_png(width: int, height: int, text: str) -> bytes:
    """
    Erzeugt ein minimales PNG (1×1 grau) als Platzhalter.
    Pillow ist optional — ohne Pillow wird ein hartkodiertes 1×1-PNG genutzt.
    """
    try:
        from PIL import Image, ImageDraw
        import io

        img = Image.new("RGB", (width, height), color=(128, 128, 128))
        draw = ImageDraw.Draw(img)
        # Ersten 80 Zeichen des Textes einzeichnen
        draw.text((10, 10), text[:80], fill=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Minimales 1×1 graues PNG (hartkodiert, RFC 2083-konform)
        return (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\x80\x80\x80\x00\x00\x00\x04\x00\x01\xf6\x17\x84\x80"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
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
        "service": "image-generation",
        "port": 8011,
        "database": {"ok": db_ok, "error": db_error},
        "ollama": ollama_status,
    }


@app.post("/generate", response_model=GeneratedImageResponse, status_code=status.HTTP_201_CREATED)
async def generate_image(req: GenerateRequest):
    """
    Generiert ein Bild via Ollama und speichert es unter
    IMAGE_STORAGE_PATH/{zone}/{uuid}.png.
    """
    # Zielverzeichnis anlegen
    zone_dir = IMAGE_STORAGE_PATH / req.zone
    zone_dir.mkdir(parents=True, exist_ok=True)

    image_id = str(uuid.uuid4())
    file_path = zone_dir / f"{image_id}.png"

    # Bild generieren
    image_bytes = await _generate_via_ollama(req.prompt, req.model, req.width, req.height)

    # Datei schreiben
    try:
        file_path.write_bytes(image_bytes)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {exc}")

    # DB-Eintrag
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO generated_images
                (id, prompt, model_used, file_path, zone, width, height, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, file_path, zone, model_used, created_at
            """,
            image_id,
            req.prompt,
            req.model,
            str(file_path),
            req.zone,
            req.width,
            req.height,
            json.dumps({"ollama_host": OLLAMA_HOST}),
        )

    return GeneratedImageResponse(
        id=row["id"],
        file_path=row["file_path"],
        zone=row["zone"],
        model=row["model_used"],
        created_at=row["created_at"],
    )


@app.get("/images", response_model=List[ImageMetadata])
async def list_images(zone: Optional[str] = None, limit: int = 50):
    """Listet generierte Bilder aus der Datenbank."""
    async with db_pool.acquire() as conn:
        if zone:
            rows = await conn.fetch(
                """
                SELECT id, prompt, model_used, file_path, zone, width, height, metadata, created_at
                FROM generated_images
                WHERE zone = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                zone,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, prompt, model_used, file_path, zone, width, height, metadata, created_at
                FROM generated_images
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

    result = []
    for row in rows:
        data = dict(row)
        raw_meta = data.get("metadata")
        if isinstance(raw_meta, str):
            try:
                data["metadata"] = json.loads(raw_meta)
            except json.JSONDecodeError:
                data["metadata"] = {}
        elif raw_meta is None:
            data["metadata"] = {}
        result.append(ImageMetadata(**data))
    return result


@app.get("/images/{image_id}", response_model=ImageMetadata)
async def get_image(image_id: str):
    """Gibt Metadaten eines einzelnen generierten Bildes zurück."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, prompt, model_used, file_path, zone, width, height, metadata, created_at
            FROM generated_images
            WHERE id = $1
            """,
            image_id,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Bild '{image_id}' nicht gefunden")

    data = dict(row)
    raw_meta = data.get("metadata")
    if isinstance(raw_meta, str):
        try:
            data["metadata"] = json.loads(raw_meta)
        except json.JSONDecodeError:
            data["metadata"] = {}
    elif raw_meta is None:
        data["metadata"] = {}
    return ImageMetadata(**data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
