from __future__ import annotations

"""
Kirobi Image Generation Service
Zone: WORKSPACE
Purpose: KI-Bildgenerierung via Ollama (llava/stable-diffusion)
Port: 8011
"""

import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
import asyncpg
import httpx
from dotenv import load_dotenv
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

try:
    from kirobi_core.analytics_client import track as _analytics_track
except Exception:  # noqa: BLE001
    async def _analytics_track(*_args, **_kwargs) -> None:  # type: ignore[misc]
        pass

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)
IMAGE_STORAGE_PATH = Path(os.getenv("IMAGE_STORAGE_PATH", "/data/images"))
try:
    IMAGE_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
except PermissionError:
    pass  # Im Container wird das Volume gemountet; außerhalb ignorieren

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
    url: Optional[str] = None
    zone: str
    model: str
    created_at: datetime


class ImageMetadata(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
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


async def _generate_via_stability(prompt: str, width: int, height: int) -> bytes:
    """Bildgenerierung via Stability AI API (wenn STABILITY_API_KEY gesetzt)."""
    import base64
    payload = {
        "text_prompts": [{"text": prompt, "weight": 1.0}],
        "cfg_scale": 7,
        "width": min(width, 1024),
        "height": min(height, 1024),
        "samples": 1,
        "steps": 30,
    }
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            json=payload,
            headers=headers,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Stability AI: HTTP {resp.status_code}")
        data = resp.json()
        return base64.b64decode(data["artifacts"][0]["base64"])


# ---------------------------------------------------------------------------
# Helper: Hübsches generatives Bild via Pillow (wenn kein API-Key verfügbar)
# ---------------------------------------------------------------------------
_DIFFUSERS_PIPE = None
_DIFFUSERS_MODEL_ID = None


def _diffusers_load(model_key: str):
    global _DIFFUSERS_PIPE, _DIFFUSERS_MODEL_ID
    key = model_key.lower()
    if key in ("sd15", "sd-1.5", "sd1.5", "stable-diffusion-1.5"):
        model_id = "runwayml/stable-diffusion-v1-5"
    else:
        model_id = "stabilityai/sdxl-turbo"

    if _DIFFUSERS_PIPE is not None and _DIFFUSERS_MODEL_ID == model_id:
        return _DIFFUSERS_PIPE

    import torch
    from diffusers import AutoPipelineForText2Image

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    try:
        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id, torch_dtype=dtype, variant="fp16"
        )
    except Exception:
        pipe = AutoPipelineForText2Image.from_pretrained(model_id, torch_dtype=dtype)
    if torch.cuda.is_available():
        # enable_model_cpu_offload: Modell bleibt auf CPU, GPU wird nur für
        # den Forward-Pass genutzt (peak VRAM ~2GB statt ~6GB).
        # Damit läuft SDXL-Turbo auch wenn Ollama gleichzeitig VRAM belegt.
        try:
            pipe.enable_model_cpu_offload()
        except Exception:
            pipe = pipe.to("cuda")
    pipe.set_progress_bar_config(disable=True)

    _DIFFUSERS_PIPE = pipe
    _DIFFUSERS_MODEL_ID = model_id
    return pipe


async def _generate_via_diffusers(prompt: str, model: str, width: int, height: int) -> bytes:
    """Echte Bildgenerierung via diffusers (SDXL-Turbo / SD 1.5) auf GPU."""
    import asyncio
    import functools
    import io

    def _sync() -> bytes:
        pipe = _diffusers_load(model)
        is_turbo = "turbo" in (_DIFFUSERS_MODEL_ID or "").lower()
        kwargs = {"prompt": prompt, "width": width, "height": height}
        if is_turbo:
            kwargs.update({"num_inference_steps": 4, "guidance_scale": 0.0})
        else:
            kwargs.update({"num_inference_steps": 25})
        img = pipe(**kwargs).images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, functools.partial(_sync))
    except Exception as exc:
        import logging
        logging.getLogger("image-generation").error(
            "diffusers inference failed: %s: %s", type(exc).__name__, exc, exc_info=True
        )
        return _make_placeholder_png(width, height, f"[diffusers error] {exc}")


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
        if resp.status_code == 404:
            # Modell nicht installiert -> graceful degradation: Placeholder-PNG
            # mit dem Original-Prompt als Beschriftung.
            return _make_placeholder_png(
                width,
                height,
                f"[{model} nicht installiert] {prompt}",
            )
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

    # Fallback: generatives Konzept-PNG mit dem Prompt
    return _make_placeholder_png(width, height, prompt)


def _make_placeholder_png(width: int, height: int, text: str) -> bytes:
    """
    Erzeugt ein ansprechendes generatives Konzept-PNG via Pillow.
    Prompt-Schlüsselwörter bestimmen das Farbschema.
    """
    try:
        import hashlib
        import io
        import math
        from PIL import Image, ImageDraw, ImageFont

        # Farbschema aus Prompt ableiten
        text_lower = text.lower()
        if any(w in text_lower for w in ["neon", "cyber", "futur", "tech", "digital", "code"]):
            c1, c2, c3 = (0, 20, 60), (0, 210, 200), (100, 0, 200)
        elif any(w in text_lower for w in ["natur", "forest", "green", "ocean", "water"]):
            c1, c2, c3 = (0, 40, 20), (0, 160, 80), (0, 100, 160)
        elif any(w in text_lower for w in ["sunset", "warm", "gold", "fire", "orange"]):
            c1, c2, c3 = (80, 0, 20), (220, 80, 0), (255, 200, 0)
        elif any(w in text_lower for w in ["aurora", "violet", "purple", "magic", "cosmic"]):
            c1, c2, c3 = (20, 0, 60), (150, 0, 200), (0, 200, 255)
        elif any(w in text_lower for w in ["family", "home", "warm", "soft", "love"]):
            c1, c2, c3 = (60, 10, 40), (200, 80, 120), (255, 150, 100)
        else:
            # Hash des Prompts für deterministisches Farbschema
            h = hashlib.md5(text.encode()).hexdigest()
            c1 = (int(h[0:2], 16) // 4, int(h[2:4], 16) // 4, int(h[4:6], 16) // 4)
            c2 = (int(h[6:8], 16), int(h[8:10], 16), int(h[10:12], 16))
            c3 = (int(h[12:14], 16), int(h[14:16], 16) // 2, 255 - int(h[16:18], 16) // 2)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Vertikaler Gradient
        for y in range(height):
            t = y / height
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Geometrische Akzente
        for i in range(5):
            angle = (i / 5) * 2 * math.pi
            cx = int(width * 0.5 + width * 0.3 * math.cos(angle))
            cy = int(height * 0.5 + height * 0.3 * math.sin(angle))
            r = int(min(width, height) * 0.15)
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=c3,
                outline=(255, 255, 255),
            )

        # Prompt-Text zentriert
        display_text = (text[:80] + "…") if len(text) > 80 else text
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/DejaVuSans.ttf",
        ]
        font = None
        font_size = max(16, width // 30)
        for fp in font_paths:
            try:
                font = ImageFont.truetype(fp, size=font_size)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()

        # Text-Hintergrund (halbtransparent simuliert via Rechteck)
        margin = width // 10
        draw.rectangle(
            [(margin, height // 2 - 50), (width - margin, height // 2 + 50)],
            fill=(0, 0, 0),
        )
        draw.text(
            (width // 2, height // 2),
            display_text,
            fill=(255, 255, 255),
            font=font,
            anchor="mm",
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
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
    Generiert ein Bild lokal via SDXL-Turbo (GPU) oder Stability AI API.
    Fallback: generatives Konzept-PNG via Pillow.
    """
    # Zielverzeichnis anlegen
    zone_dir = IMAGE_STORAGE_PATH / req.zone
    zone_dir.mkdir(parents=True, exist_ok=True)

    image_id = str(uuid.uuid4())
    file_path = zone_dir / f"{image_id}.png"

    # Bild generieren — Priorität:
    # 1. Lokale diffusers/SDXL-Turbo (immer bevorzugt, 100% lokal, RTX 3090)
    # 2. Stability AI API (nur wenn STABILITY_API_KEY gesetzt und lokale Generierung fehlschlägt)
    # 3. Generatives Pillow-Konzept-PNG (Fallback)
    model_lc = req.model.lower()

    # Modell-Auswahl für diffusers
    if model_lc in ("sd15", "sd-1.5", "stable-diffusion-1.5"):
        diffusers_model = "sd15"
    else:
        diffusers_model = "sdxl-turbo"  # Standard: SDXL-Turbo

    try:
        image_bytes = await _generate_via_diffusers(req.prompt, diffusers_model, req.width, req.height)
        used_model = _DIFFUSERS_MODEL_ID or diffusers_model
    except Exception:
        if STABILITY_API_KEY:
            try:
                image_bytes = await _generate_via_stability(req.prompt, req.width, req.height)
                used_model = "stability-ai"
            except Exception:
                image_bytes = _make_placeholder_png(req.width, req.height, req.prompt)
                used_model = req.model or "pillow-placeholder"
        else:
            image_bytes = _make_placeholder_png(req.width, req.height, req.prompt)
            used_model = req.model or "pillow-placeholder"

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
            used_model,
            str(file_path),
            req.zone,
            req.width,
            req.height,
            json.dumps({"ollama_host": OLLAMA_HOST}),
        )

    asyncio.create_task(_analytics_track("image_generation", zone=req.zone, model=req.model))
    return GeneratedImageResponse(
        id=row["id"],
        file_path=row["file_path"],
        url=f"/file/{image_id}",
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


@app.get("/file/{image_id}")
async def serve_image_file(image_id: str):
    """Liefert die generierte Bilddatei aus."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_path FROM generated_images WHERE id = $1", image_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Bild nicht gefunden")
    fp = Path(row["file_path"])
    if not fp.exists():
        raise HTTPException(status_code=410, detail="Datei nicht mehr verfuegbar")
    return FileResponse(fp, media_type="image/png", filename=fp.name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
