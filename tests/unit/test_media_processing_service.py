"""
Unit-Tests für services/media-processing/main.py
Zone: WORKSPACE

Pillow und mutagen werden vollständig gemockt.
Kein echter Datei-I/O, keine externen Abhängigkeiten erforderlich.
"""
from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Minimal-PNG für Tests (1×1 grau, hartkodiert)
# ---------------------------------------------------------------------------
_MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\x80\x80\x80\x00\x00\x00\x04\x00\x01\xf6\x17\x84\x80"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """TestClient für den Media-Processing-Service (echte Bibliotheken)."""
    import services.media_processing.main as svc
    with TestClient(svc.app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Health-Endpoint
# ---------------------------------------------------------------------------

def test_health_returns_healthy(client):
    """GET /health muss 'healthy' zurückgeben."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "media-processing"
    assert data["port"] == 8012
    assert "capabilities" in data
    assert "image_processing" in data["capabilities"]
    assert "audio_metadata" in data["capabilities"]


# ---------------------------------------------------------------------------
# GET /formats
# ---------------------------------------------------------------------------

def test_formats_endpoint_returns_lists(client):
    """GET /formats muss Listen mit unterstützten Formaten zurückgeben."""
    resp = client.get("/formats")
    assert resp.status_code == 200
    data = resp.json()
    assert "image_formats" in data
    assert "audio_formats" in data
    assert "pillow_available" in data
    assert "mutagen_available" in data
    assert isinstance(data["image_formats"], list)
    assert isinstance(data["audio_formats"], list)


# ---------------------------------------------------------------------------
# POST /process/image — ohne Pillow
# ---------------------------------------------------------------------------

def test_process_image_without_pillow_returns_503():
    """POST /process/image muss 503 zurückgeben wenn Pillow nicht verfügbar."""
    import services.media_processing.main as svc

    with patch.object(svc, "_PILLOW_AVAILABLE", False):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/image",
                files={"file": ("test.png", _MINIMAL_PNG, "image/png")},
                data={"width": "64", "height": "64", "output_format": "PNG"},
            )

    assert resp.status_code == 503
    assert "Pillow" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /process/image — ungültiges Format
# ---------------------------------------------------------------------------

def test_process_image_invalid_format_returns_400():
    """POST /process/image mit ungültigem Format muss 400 zurückgeben."""
    import services.media_processing.main as svc

    with patch.object(svc, "_PILLOW_AVAILABLE", True):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/image",
                files={"file": ("test.png", _MINIMAL_PNG, "image/png")},
                data={"width": "64", "height": "64", "output_format": "INVALID"},
            )

    assert resp.status_code == 400
    assert "INVALID" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /process/image — ungültige Datei
# ---------------------------------------------------------------------------

def test_process_image_invalid_file_returns_400():
    """POST /process/image mit ungültiger Datei muss 400 zurückgeben."""
    import services.media_processing.main as svc

    # Pillow muss verfügbar sein, aber open() schlägt fehl
    with patch.object(svc, "_PILLOW_AVAILABLE", True), \
         patch("services.media_processing.main.PILImage") as mock_pil:
        mock_pil.open.side_effect = Exception("cannot identify image file")
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/image",
                files={"file": ("broken.png", b"not-an-image", "image/png")},
                data={"width": "64", "height": "64", "output_format": "PNG"},
            )

    assert resp.status_code == 400
    assert "Ungültige Bilddatei" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /process/image — Erfolg
# ---------------------------------------------------------------------------

def test_process_image_success():
    """POST /process/image muss 200 und base64-kodiertes Bild zurückgeben."""
    import services.media_processing.main as svc

    # Mock PIL Image
    mock_img = MagicMock()
    mock_img.mode = "RGB"
    resized_img = MagicMock()
    resized_img.mode = "RGB"
    mock_img.resize = MagicMock(return_value=resized_img)

    # save() schreibt echte PNG-Bytes in den Buffer
    def fake_save(buf, format):
        buf.write(_MINIMAL_PNG)

    resized_img.save = fake_save

    with patch.object(svc, "_PILLOW_AVAILABLE", True), \
         patch("services.media_processing.main.PILImage") as mock_pil:
        mock_pil.open.return_value = mock_img
        mock_pil.LANCZOS = 1

        # ImageOps.exif_transpose mocken
        mock_img_ops = MagicMock()
        mock_img_ops.exif_transpose = MagicMock(return_value=mock_img)

        with patch.dict("sys.modules", {"PIL.ImageOps": mock_img_ops}):
            with TestClient(svc.app, raise_server_exceptions=False) as c:
                resp = c.post(
                    "/process/image",
                    files={"file": ("test.png", _MINIMAL_PNG, "image/png")},
                    data={"width": "64", "height": "64", "output_format": "PNG"},
                )

    assert resp.status_code == 200
    data = resp.json()
    assert "image_base64" in data
    assert data["processed_width"] == 64
    assert data["processed_height"] == 64
    assert data["output_format"] == "PNG"
    assert data["mime_type"] == "image/png"


# ---------------------------------------------------------------------------
# POST /process/audio/metadata — ohne mutagen
# ---------------------------------------------------------------------------

def test_audio_metadata_without_mutagen():
    """POST /process/audio/metadata muss Fallback-Response ohne mutagen liefern."""
    import services.media_processing.main as svc

    with patch.object(svc, "_MUTAGEN_AVAILABLE", False):
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/audio/metadata",
                files={"file": ("test.mp3", b"\xff\xfb\x90\x00" * 100, "audio/mpeg")},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["mutagen_available"] is False
    assert data["filename"] == "test.mp3"
    assert data["duration_seconds"] is None
    assert data["bitrate_kbps"] is None


# ---------------------------------------------------------------------------
# POST /process/audio/metadata — ungültige Datei
# ---------------------------------------------------------------------------

def test_audio_metadata_invalid_file_returns_400():
    """POST /process/audio/metadata mit korrupter Datei muss 400 zurückgeben."""
    import services.media_processing.main as svc

    with patch.object(svc, "_MUTAGEN_AVAILABLE", True), \
         patch("services.media_processing.main.MutagenFile") as mock_mutagen:
        mock_mutagen.side_effect = Exception("not a valid audio file")
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/audio/metadata",
                files={"file": ("broken.mp3", b"not-audio", "audio/mpeg")},
            )

    assert resp.status_code == 400
    assert "gelesen werden" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /process/audio/metadata — unbekanntes Format
# ---------------------------------------------------------------------------

def test_audio_metadata_unknown_format_returns_400():
    """POST /process/audio/metadata mit unbekanntem Format muss 400 zurückgeben."""
    import services.media_processing.main as svc

    with patch.object(svc, "_MUTAGEN_AVAILABLE", True), \
         patch("services.media_processing.main.MutagenFile") as mock_mutagen:
        # mutagen gibt None zurück für unbekannte Formate
        mock_mutagen.return_value = None
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/audio/metadata",
                files={"file": ("unknown.xyz", b"\x00\x01\x02\x03", "application/octet-stream")},
            )

    assert resp.status_code == 400
    assert "Unbekanntes Audio-Format" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# POST /process/audio/metadata — Erfolg
# ---------------------------------------------------------------------------

def test_audio_metadata_success():
    """POST /process/audio/metadata muss Metadaten zurückgeben wenn mutagen verfügbar."""
    import services.media_processing.main as svc

    # Mock mutagen Audio-Objekt
    mock_info = MagicMock()
    mock_info.length = 180.5
    mock_info.bitrate = 128000
    mock_info.sample_rate = 44100
    mock_info.channels = 2

    mock_audio = MagicMock()
    mock_audio.info = mock_info
    mock_audio.tags = {"TIT2": "Test Song", "TPE1": "Test Artist"}

    with patch.object(svc, "_MUTAGEN_AVAILABLE", True), \
         patch("services.media_processing.main.MutagenFile") as mock_mutagen:
        mock_mutagen.return_value = mock_audio
        with TestClient(svc.app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/process/audio/metadata",
                files={"file": ("song.mp3", b"\xff\xfb\x90\x00" * 100, "audio/mpeg")},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["mutagen_available"] is True
    assert data["filename"] == "song.mp3"
    assert data["duration_seconds"] == 180.5
    assert data["bitrate_kbps"] == 128
    assert data["sample_rate_hz"] == 44100
    assert data["channels"] == 2
    assert "TIT2" in data["tags"]
