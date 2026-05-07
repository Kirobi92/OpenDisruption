---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Service: media-processing

Medien-Verarbeitung für das Kirobi-System — Bilder skalieren/konvertieren und Audio-Metadaten extrahieren.

## Was dieser Service tut

Stellt zwei unabhängige Verarbeitungs-Pipelines bereit:

1. **Bild-Verarbeitung** (via Pillow): Upload → Resize auf Zielgröße → Ausgabe als base64-kodierter PNG/JPEG/WEBP
2. **Audio-Metadaten** (via mutagen): Upload → Dauer, Bitrate, Sample-Rate, Kanäle, Tags extrahieren

Beide Pipelines haben graceful Fallbacks: ohne Pillow/mutagen gibt der Service HTTP 503 zurück, anstatt zu crashen.

## API-Endpoints

| Method | Pfad | Beschreibung |
|--------|------|--------------|
| `GET` | `/health` | Service-Status + verfügbare Bibliotheken |
| `GET` | `/formats` | Unterstützte Bild- und Audio-Formate |
| `POST` | `/process/image` | Bild hochladen, skalieren, als base64 zurückgeben |
| `POST` | `/process/audio/metadata` | Audio-Metadaten extrahieren |

## Konfiguration (Env-Variablen)

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `KIROBI_PUBLIC_ORIGINS` | — | CORS-Whitelist (leer = LAN-Regex) |

## Starten / Testen

```bash
# Im Container
docker compose up media-processing

# Health-Check
curl http://localhost:8012/health

# Bild skalieren (multipart/form-data)
curl -X POST http://localhost:8012/process/image \
  -F "file=@bild.jpg" \
  -F "width=256" \
  -F "height=256" \
  -F "output_format=PNG"
```

## Bekannte Einschränkungen

- Kein Datei-Speicher: verarbeitete Bilder werden als base64 zurückgegeben, nicht persistiert
- EXIF-Rotation wird automatisch korrigiert (Pillow `exif_transpose`)
- JPEG-Output erfordert RGB-Modus — RGBA/P wird automatisch konvertiert
- Port: `8012`
