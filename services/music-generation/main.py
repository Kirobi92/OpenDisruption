from __future__ import annotations

"""
Kirobi Music Generation Service
Zone: WORKSPACE
Purpose: KI-Musikgenerierung via Ollama (Prompt-Enhancement) + MusicGen/AudioCraft (optional)
Port: 8013
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

load_dotenv()

try:
    from kirobi_core.analytics_client import track as _analytics_track
except Exception:  # noqa: BLE001
    async def _analytics_track(*_args, **_kwargs) -> None:  # type: ignore[misc]
        pass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("MUSIC_OLLAMA_MODEL", "llama3.2:3b")
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)
AUDIO_STORAGE_PATH = Path(os.getenv("AUDIO_STORAGE_PATH", "/data/audio"))
try:
    AUDIO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
except PermissionError:
    pass  # Im Container wird das Volume gemountet; außerhalb ignorieren

# AudioCraft/MusicGen verfügbar?
_AUDIOCRAFT_AVAILABLE = False
try:
    import audiocraft  # noqa: F401
    _AUDIOCRAFT_AVAILABLE = True
except ImportError:
    pass

# HeartMuLa verfügbar?
_HEARTMULA_AVAILABLE = False
_HEARTMULA_MODEL_PATH = Path(os.getenv("HEARTMULA_MODEL_PATH", "/data/models/heartmula"))
try:
    import heartlib  # noqa: F401
    if _HEARTMULA_MODEL_PATH.exists():
        _HEARTMULA_AVAILABLE = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# DB schema
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS generated_tracks (
    id              TEXT PRIMARY KEY,
    prompt          TEXT NOT NULL,
    enhanced_prompt TEXT,
    genre           TEXT,
    duration_seconds INT,
    model_used      TEXT,
    file_path       TEXT NOT NULL,
    zone            TEXT NOT NULL,
    is_placeholder  BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS generated_tracks_zone_idx
    ON generated_tracks(zone);
CREATE INDEX IF NOT EXISTS generated_tracks_created_idx
    ON generated_tracks(created_at DESC);
CREATE INDEX IF NOT EXISTS generated_tracks_genre_idx
    ON generated_tracks(genre);
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
    prompt: str = Field(..., min_length=1, description="Musik-Beschreibungs-Prompt")
    duration_seconds: int = Field(30, ge=5, le=300, description="Gewünschte Dauer in Sekunden")
    genre: str = Field("ambient", description="Musikgenre (z.B. ambient, jazz, electronic)")
    zone: str = Field("WORKSPACE", description="Sicherheitszone")


class GeneratedTrackResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    file_path: str
    zone: str
    model_used: str
    enhanced_prompt: Optional[str]
    genre: str
    duration_seconds: int
    is_placeholder: bool
    created_at: datetime


class TrackMetadata(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    prompt: str
    enhanced_prompt: Optional[str]
    genre: Optional[str]
    duration_seconds: Optional[int]
    model_used: Optional[str]
    file_path: str
    zone: str
    is_placeholder: bool
    metadata: dict
    created_at: datetime


class HeartMuLaRequest(BaseModel):
    lyrics: str = Field(..., description="Liedtext (Multiline)")
    tags: str = Field("pop, uplifting", description="Genre, Stimmung, BPM z.B. 'pop, happy, 120bpm'")
    max_audio_length_ms: int = Field(240_000, ge=10_000, le=600_000)
    temperature: float = Field(1.0, ge=0.1, le=2.0)
    cfg_scale: float = Field(1.5, ge=0.5, le=5.0)
    topk: int = Field(50, ge=1, le=200)
    zone: str = Field("WORKSPACE")


class HeartMuLaTranscribeRequest(BaseModel):
    track_id: str = Field(..., description="ID eines generierten Tracks")


class HeartMuLaStatusResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    available: bool
    model_path: str
    model_exists: bool
    message: str


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
    title="Kirobi Music Generation Service",
    description="KI-Musikgenerierung via Ollama Prompt-Enhancement + MusicGen/AudioCraft — Zone: WORKSPACE",
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
# Helper: Prompt via Ollama verbessern (Text-to-Music-Prompt-Enhancement)
# ---------------------------------------------------------------------------
async def _enhance_prompt_via_ollama(
    prompt: str,
    genre: str,
    duration_seconds: int,
) -> str:
    """
    Nutzt Ollama um den Musik-Prompt für MusicGen zu optimieren.
    Gibt einen detaillierten, englischsprachigen MusicGen-Prompt zurück.
    """
    system_instruction = (
        "You are a music prompt engineer specializing in AI music generation. "
        "Your task is to enhance a user's music description into a detailed, "
        "technical prompt suitable for MusicGen/AudioCraft. "
        "Include: instrumentation, tempo, mood, key, texture, dynamics. "
        "Keep the enhanced prompt under 200 words. Respond ONLY with the enhanced prompt, no explanations."
    )
    user_message = (
        f"Enhance this music prompt for AI generation:\n"
        f"Original: {prompt}\n"
        f"Genre: {genre}\n"
        f"Duration: {duration_seconds} seconds\n\n"
        f"Enhanced prompt:"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system_instruction}\n\n{user_message}",
        "stream": False,
        "options": {
            "num_predict": 300,
            "temperature": 0.7,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                enhanced = data.get("response", "").strip()
                return enhanced if enhanced else prompt
            # Ollama nicht erreichbar oder Fehler → Original-Prompt verwenden
            return prompt
        except Exception:
            return prompt


# ---------------------------------------------------------------------------
# Helper: Musik via AudioCraft/MusicGen generieren
# ---------------------------------------------------------------------------
async def _generate_via_audiocraft(
    enhanced_prompt: str,
    duration_seconds: int,
    file_path: Path,
) -> bool:
    """
    Versucht Musik via AudioCraft/MusicGen zu generieren.
    Gibt True zurück wenn erfolgreich, False wenn AudioCraft nicht verfügbar.
    """
    if not _AUDIOCRAFT_AVAILABLE:
        return False

    try:
        # AudioCraft ist synchron — in einem Thread-Pool ausführen
        import asyncio
        import functools

        def _sync_generate() -> None:
            from audiocraft.models import MusicGen
            from audiocraft.data.audio import audio_write

            model = MusicGen.get_pretrained("facebook/musicgen-small")
            model.set_generation_params(duration=duration_seconds)
            wav = model.generate([enhanced_prompt])
            # audio_write erwartet Pfad ohne Extension
            audio_write(
                str(file_path.with_suffix("")),
                wav[0].cpu(),
                model.sample_rate,
                strategy="loudness",
            )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, functools.partial(_sync_generate))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Helper: Placeholder-Audio (minimale WAV-Datei)
# ---------------------------------------------------------------------------
def _make_placeholder_wav(duration_seconds: int, enhanced_prompt: str) -> bytes:
    """
    Erzeugt eine minimale WAV-Datei als Platzhalter wenn AudioCraft nicht verfügbar ist.
    Enthält Stille mit korrektem WAV-Header für die angegebene Dauer.
    """
    import struct

    sample_rate = 22050
    num_channels = 1
    bits_per_sample = 16
    num_samples = sample_rate * min(duration_seconds, 10)  # max 10s Stille
    data_size = num_samples * num_channels * (bits_per_sample // 8)

    # WAV-Header (RIFF/PCM)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,                  # Chunk-Größe
        1,                   # PCM
        num_channels,
        sample_rate,
        sample_rate * num_channels * (bits_per_sample // 8),  # Byte-Rate
        num_channels * (bits_per_sample // 8),                # Block-Align
        bits_per_sample,
        b"data",
        data_size,
    )
    # Stille (Nullen)
    audio_data = b"\x00" * data_size
    return header + audio_data


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health-Check: prüft DB, Ollama-Erreichbarkeit und AudioCraft-Verfügbarkeit."""
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
        "service": "music-generation",
        "port": 8013,
        "database": {"ok": db_ok, "error": db_error},
        "ollama": ollama_status,
        "audiocraft": {
            "available": _AUDIOCRAFT_AVAILABLE,
            "note": "Placeholder-WAV wird genutzt wenn AudioCraft nicht installiert ist",
        },
    }


@app.post(
    "/generate",
    response_model=GeneratedTrackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_track(req: GenerateRequest):
    """
    Generiert einen Musik-Track:
    1. Prompt-Enhancement via Ollama
    2. Audiogenerierung via AudioCraft/MusicGen (falls verfügbar)
    3. Graceful Fallback auf Placeholder-WAV wenn AudioCraft fehlt
    4. Speichert Metadaten in PostgreSQL
    """
    # Zielverzeichnis anlegen
    zone_dir = AUDIO_STORAGE_PATH / req.zone
    try:
        zone_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass  # Volume-Mount im Container

    track_id = str(uuid.uuid4())
    file_path = zone_dir / f"{track_id}.wav"

    # 1. Prompt via Ollama verbessern
    enhanced_prompt = await _enhance_prompt_via_ollama(
        req.prompt, req.genre, req.duration_seconds
    )

    # 2. Musik generieren (AudioCraft oder Placeholder)
    is_placeholder = True
    model_used = "placeholder"

    audiocraft_success = await _generate_via_audiocraft(
        enhanced_prompt, req.duration_seconds, file_path
    )

    if audiocraft_success:
        is_placeholder = False
        model_used = "facebook/musicgen-small"
    else:
        # Fallback: Placeholder-WAV schreiben
        wav_bytes = _make_placeholder_wav(req.duration_seconds, enhanced_prompt)
        try:
            file_path.write_bytes(wav_bytes)
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Fehler beim Speichern der Audio-Datei: {exc}",
            )

    # 3. DB-Eintrag
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO generated_tracks
                (id, prompt, enhanced_prompt, genre, duration_seconds,
                 model_used, file_path, zone, is_placeholder, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, file_path, zone, model_used, enhanced_prompt,
                      genre, duration_seconds, is_placeholder, created_at
            """,
            track_id,
            req.prompt,
            enhanced_prompt,
            req.genre,
            req.duration_seconds,
            model_used,
            str(file_path),
            req.zone,
            is_placeholder,
            json.dumps({
                "ollama_host": OLLAMA_HOST,
                "ollama_model": OLLAMA_MODEL,
                "audiocraft_available": _AUDIOCRAFT_AVAILABLE,
            }),
        )

    asyncio.create_task(_analytics_track("music_generation", zone=req.zone, model=model_used))
    return GeneratedTrackResponse(
        id=row["id"],
        file_path=row["file_path"],
        zone=row["zone"],
        model_used=row["model_used"],
        enhanced_prompt=row["enhanced_prompt"],
        genre=row["genre"],
        duration_seconds=row["duration_seconds"],
        is_placeholder=row["is_placeholder"],
        created_at=row["created_at"],
    )


@app.get("/tracks", response_model=List[TrackMetadata])
async def list_tracks(
    zone: Optional[str] = None,
    genre: Optional[str] = None,
    limit: int = 50,
):
    """Listet generierte Tracks aus der Datenbank, optional gefiltert nach Zone und Genre."""
    async with db_pool.acquire() as conn:
        if zone and genre:
            rows = await conn.fetch(
                """
                SELECT id, prompt, enhanced_prompt, genre, duration_seconds,
                       model_used, file_path, zone, is_placeholder, metadata, created_at
                FROM generated_tracks
                WHERE zone = $1 AND genre = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                zone,
                genre,
                limit,
            )
        elif zone:
            rows = await conn.fetch(
                """
                SELECT id, prompt, enhanced_prompt, genre, duration_seconds,
                       model_used, file_path, zone, is_placeholder, metadata, created_at
                FROM generated_tracks
                WHERE zone = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                zone,
                limit,
            )
        elif genre:
            rows = await conn.fetch(
                """
                SELECT id, prompt, enhanced_prompt, genre, duration_seconds,
                       model_used, file_path, zone, is_placeholder, metadata, created_at
                FROM generated_tracks
                WHERE genre = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                genre,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, prompt, enhanced_prompt, genre, duration_seconds,
                       model_used, file_path, zone, is_placeholder, metadata, created_at
                FROM generated_tracks
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
        result.append(TrackMetadata(**data))
    return result


@app.get("/tracks/{track_id}", response_model=TrackMetadata)
async def get_track(track_id: str):
    """Gibt Metadaten eines einzelnen generierten Tracks zurück."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, prompt, enhanced_prompt, genre, duration_seconds,
                   model_used, file_path, zone, is_placeholder, metadata, created_at
            FROM generated_tracks
            WHERE id = $1
            """,
            track_id,
        )

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Track '{track_id}' nicht gefunden",
        )

    data = dict(row)
    raw_meta = data.get("metadata")
    if isinstance(raw_meta, str):
        try:
            data["metadata"] = json.loads(raw_meta)
        except json.JSONDecodeError:
            data["metadata"] = {}
    elif raw_meta is None:
        data["metadata"] = {}
    return TrackMetadata(**data)


@app.get("/file/{track_id}")
async def serve_track_file(track_id: str):
    """Liefert die generierte WAV-Datei aus."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_path FROM generated_tracks WHERE id = $1", track_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Track nicht gefunden")
    fp = Path(row["file_path"])
    if not fp.exists():
        raise HTTPException(status_code=410, detail="Datei nicht mehr verfuegbar")
    return FileResponse(fp, media_type="audio/wav", filename=fp.name)


@app.get("/heartmula/status", response_model=HeartMuLaStatusResponse)
async def heartmula_status():
    """Prüft ob HeartMuLa Model verfügbar ist."""
    model_exists = _HEARTMULA_MODEL_PATH.exists()
    return HeartMuLaStatusResponse(
        available=_HEARTMULA_AVAILABLE,
        model_path=str(_HEARTMULA_MODEL_PATH),
        model_exists=model_exists,
        message=(
            "HeartMuLa bereit" if _HEARTMULA_AVAILABLE else
            f"Model nicht gefunden unter {_HEARTMULA_MODEL_PATH}. Lade mit: pip install heartlib und lade das Modell herunter."
        ),
    )


@app.post("/heartmula/generate")
async def heartmula_generate(req: HeartMuLaRequest):
    """
    Generiert Musik via HeartMuLa (lyrics-konditioniert).
    Fallback: MusicGen/Placeholder falls Modell nicht verfügbar.
    """
    track_id = str(uuid.uuid4())
    out_path = AUDIO_STORAGE_PATH / f"{track_id}.wav"

    if _HEARTMULA_AVAILABLE:
        import torch
        from heartlib import HeartMuLaGenPipeline

        def _sync_generate_heartmula() -> None:
            pipe = HeartMuLaGenPipeline.from_pretrained(
                str(_HEARTMULA_MODEL_PATH),
                device={"mula": torch.device("cuda"), "codec": torch.device("cuda")},
                dtype={"mula": torch.bfloat16, "codec": torch.float32},
                version="3B",
                lazy_load=True,
            )
            with torch.no_grad():
                pipe(
                    {"lyrics": req.lyrics, "tags": req.tags},
                    max_audio_length_ms=req.max_audio_length_ms,
                    save_path=str(out_path),
                    topk=req.topk,
                    temperature=req.temperature,
                    cfg_scale=req.cfg_scale,
                )

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_generate_heartmula)
        model_used = "heartmula-3b"
    else:
        # Fallback: Placeholder WAV + Prompt-Enhancement
        prompt = f"lyrics-based music: {req.tags}\n{req.lyrics[:200]}"
        enhanced = await _enhance_prompt_via_ollama(
            prompt,
            "music_generation",
            int(req.max_audio_length_ms / 1000),
        )
        wav_bytes = _make_placeholder_wav(int(req.max_audio_length_ms / 1000), enhanced)
        out_path.write_bytes(wav_bytes)
        model_used = "placeholder (heartmula-unavailable)"

    duration_s = req.max_audio_length_ms // 1000

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO generated_tracks
                (id, prompt, enhanced_prompt, genre, duration_seconds, model_used, file_path, zone, is_placeholder, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            track_id,
            req.lyrics[:500],
            req.tags,
            req.tags,
            duration_s,
            model_used,
            str(out_path),
            req.zone,
            not _HEARTMULA_AVAILABLE,
            json.dumps({"source": "heartmula", "temperature": req.temperature, "cfg_scale": req.cfg_scale}),
        )

    await _analytics_track(
        "heartmula_generate",
        zone=req.zone,
        model=model_used,
        metadata={"source": "heartmula"},
    )

    return {
        "id": track_id,
        "model_used": model_used,
        "duration_seconds": duration_s,
        "file_url": f"/file/{track_id}",
        "is_placeholder": not _HEARTMULA_AVAILABLE,
        "zone": req.zone,
    }


@app.post("/heartmula/transcribe")
async def heartmula_transcribe(req: HeartMuLaTranscribeRequest):
    """
    Transkribiert Lyrics aus einem vorhandenen Track via HeartTranscriptor.
    Fallback: Whisper aus voice-processing wenn HeartMuLa nicht verfügbar.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT file_path FROM generated_tracks WHERE id = $1", req.track_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Track nicht gefunden")

    fp = Path(row["file_path"])
    if not fp.exists():
        raise HTTPException(status_code=410, detail="Datei nicht verfügbar")

    if _HEARTMULA_AVAILABLE:
        import torch
        from heartlib import HeartTranscriptorPipeline

        transcriptor_path = _HEARTMULA_MODEL_PATH / "transcriptor"
        if not transcriptor_path.exists():
            raise HTTPException(status_code=503, detail="HeartTranscriptor Modell nicht gefunden")

        def _sync_transcribe() -> str:
            pipe = HeartTranscriptorPipeline.from_pretrained(
                str(transcriptor_path),
                device=torch.device("cuda"),
                dtype=torch.float16,
            )
            with torch.no_grad():
                result = pipe(
                    str(fp),
                    max_new_tokens=256,
                    num_beams=2,
                    task="transcribe",
                    condition_on_prev_tokens=False,
                    compression_ratio_threshold=1.8,
                    temperature=(0.0, 0.1, 0.2, 0.4),
                    logprob_threshold=-1.0,
                    no_speech_threshold=0.4,
                )
            return str(result)

        loop = asyncio.get_event_loop()
        lyrics = await loop.run_in_executor(None, _sync_transcribe)
        engine = "hearttranscriptor"
    else:
        lyrics = "[HeartTranscriptor nicht verfügbar — lade das HeartMuLa Modell herunter]"
        engine = "unavailable"

    return {"track_id": req.track_id, "lyrics": lyrics, "engine": engine}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
