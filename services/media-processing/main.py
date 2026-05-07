"""
Kirobi Media Processing Service
Zone: WORKSPACE
Purpose: Medien-Verarbeitung — Bilder resize/convert, Audio-Metadaten
Port: 8012
"""

import io
import os
import base64
import mimetypes
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Optionale Abhängigkeiten — graceful fallback
# ---------------------------------------------------------------------------
try:
    from PIL import Image as PILImage
    _PILLOW_AVAILABLE = True
except ImportError:
    PILImage = None  # type: ignore[assignment]
    _PILLOW_AVAILABLE = False

try:
    import mutagen
    from mutagen import File as MutagenFile
    _MUTAGEN_AVAILABLE = True
except ImportError:
    mutagen = None  # type: ignore[assignment]
    MutagenFile = None  # type: ignore[assignment]
    _MUTAGEN_AVAILABLE = False

# ---------------------------------------------------------------------------
# Unterstützte Formate
# ---------------------------------------------------------------------------
_SUPPORTED_IMAGE_FORMATS = ["JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF"]
_SUPPORTED_AUDIO_FORMATS = ["mp3", "flac", "ogg", "wav", "m4a", "aac", "opus"]

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
# Pydantic models
# ---------------------------------------------------------------------------
class ImageProcessResult(BaseModel):
    original_filename: str
    original_size_bytes: int
    processed_width: int
    processed_height: int
    output_format: str
    image_base64: str
    mime_type: str


class AudioMetadataResult(BaseModel):
    filename: str
    file_size_bytes: int
    mime_type: Optional[str]
    duration_seconds: Optional[float]
    bitrate_kbps: Optional[int]
    sample_rate_hz: Optional[int]
    channels: Optional[int]
    format_name: Optional[str]
    tags: dict
    mutagen_available: bool


class SupportedFormats(BaseModel):
    image_formats: List[str]
    audio_formats: List[str]
    pillow_available: bool
    mutagen_available: bool


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Kirobi Media Processing Service",
    description="Medien-Verarbeitung: Bilder resize/convert, Audio-Metadaten — Zone: WORKSPACE",
    version="1.0.0",
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
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Health-Check: gibt Service-Status und verfügbare Bibliotheken zurück."""
    return {
        "status": "healthy",
        "service": "media-processing",
        "port": 8012,
        "capabilities": {
            "image_processing": _PILLOW_AVAILABLE,
            "audio_metadata": _MUTAGEN_AVAILABLE,
        },
    }


@app.get("/formats", response_model=SupportedFormats)
async def list_formats():
    """Listet alle unterstützten Medienformate auf."""
    return SupportedFormats(
        image_formats=_SUPPORTED_IMAGE_FORMATS if _PILLOW_AVAILABLE else [],
        audio_formats=_SUPPORTED_AUDIO_FORMATS if _MUTAGEN_AVAILABLE else [],
        pillow_available=_PILLOW_AVAILABLE,
        mutagen_available=_MUTAGEN_AVAILABLE,
    )


@app.post("/process/image", response_model=ImageProcessResult)
async def process_image(
    file: UploadFile = File(..., description="Bild-Datei (JPEG, PNG, WEBP, …)"),
    width: int = Form(512, ge=1, le=8192, description="Zielbreite in Pixeln"),
    height: int = Form(512, ge=1, le=8192, description="Zielhöhe in Pixeln"),
    output_format: str = Form("PNG", description="Ausgabeformat: PNG, JPEG, WEBP"),
):
    """
    Lädt ein Bild hoch, skaliert es auf width×height und gibt es als
    base64-kodierten String zurück.

    Benötigt Pillow. Ohne Pillow wird HTTP 503 zurückgegeben.
    """
    if not _PILLOW_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Pillow ist nicht installiert. "
                "Bitte 'pip install Pillow' ausführen oder das Docker-Image neu bauen."
            ),
        )

    output_format = output_format.upper()
    if output_format not in _SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstütztes Format '{output_format}'. "
                   f"Erlaubt: {_SUPPORTED_IMAGE_FORMATS}",
        )

    raw = await file.read()
    original_size = len(raw)

    try:
        img = PILImage.open(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Ungültige Bilddatei: {exc}")

    # EXIF-Rotation berücksichtigen
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # Kein EXIF — ignorieren

    # Resize mit LANCZOS (hohe Qualität)
    img = img.resize((width, height), PILImage.LANCZOS)

    # JPEG benötigt RGB (kein Alpha-Kanal)
    if output_format == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format=output_format)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")

    mime_map = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
        "GIF": "image/gif",
        "BMP": "image/bmp",
        "TIFF": "image/tiff",
    }

    return ImageProcessResult(
        original_filename=file.filename or "upload",
        original_size_bytes=original_size,
        processed_width=width,
        processed_height=height,
        output_format=output_format,
        image_base64=encoded,
        mime_type=mime_map.get(output_format, "application/octet-stream"),
    )


@app.post("/process/audio/metadata", response_model=AudioMetadataResult)
async def audio_metadata(
    file: UploadFile = File(..., description="Audio-Datei (MP3, FLAC, OGG, WAV, …)"),
):
    """
    Extrahiert Metadaten aus einer Audio-Datei.

    Mit mutagen: Dauer, Bitrate, Sample-Rate, Kanäle, Tags.
    Ohne mutagen: Datei-Größe + MIME-Type als Fallback.
    """
    raw = await file.read()
    file_size = len(raw)
    filename = file.filename or "upload"

    # MIME-Type bestimmen
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type and file.content_type:
        mime_type = file.content_type

    if not _MUTAGEN_AVAILABLE:
        return AudioMetadataResult(
            filename=filename,
            file_size_bytes=file_size,
            mime_type=mime_type,
            duration_seconds=None,
            bitrate_kbps=None,
            sample_rate_hz=None,
            channels=None,
            format_name=None,
            tags={},
            mutagen_available=False,
        )

    # mutagen aus Byte-Buffer lesen
    try:
        audio = MutagenFile(io.BytesIO(raw), filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Audio-Datei konnte nicht gelesen werden: {exc}",
        )

    if audio is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekanntes Audio-Format für Datei '{filename}'.",
        )

    # Metadaten extrahieren
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format_name: Optional[str] = type(audio).__name__

    info = getattr(audio, "info", None)
    if info:
        duration = getattr(info, "length", None)
        raw_bitrate = getattr(info, "bitrate", None)
        if raw_bitrate:
            bitrate = raw_bitrate // 1000  # bps → kbps
        sample_rate = getattr(info, "sample_rate", None)
        channels = getattr(info, "channels", None)

    # Tags als einfaches Dict
    tags: dict = {}
    if audio.tags:
        for key, val in audio.tags.items():
            try:
                tags[str(key)] = str(val)
            except Exception:
                pass

    return AudioMetadataResult(
        filename=filename,
        file_size_bytes=file_size,
        mime_type=mime_type,
        duration_seconds=round(duration, 3) if duration is not None else None,
        bitrate_kbps=bitrate,
        sample_rate_hz=sample_rate,
        channels=channels,
        format_name=format_name,
        tags=tags,
        mutagen_available=True,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
