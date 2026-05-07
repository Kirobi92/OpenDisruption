---
zone: WORKSPACE
created_by: kirobi-coder
created_at: 2026-05-08
version: 1.0.0
---

# Kirobi Video Generation Service

**Port:** 8014  
**Zone:** WORKSPACE  
**Zweck:** Asynchrone KI-Videogenerierung via Ollama (Text-to-Video-Prompts)

## Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/health` | Health-Check (DB + Ollama) |
| `POST` | `/generate` | Neuen Video-Job erstellen (async) |
| `GET` | `/jobs/{job_id}` | Job-Status abfragen |
| `GET` | `/jobs` | Alle Jobs des Users (Header: `X-User-Id`) |
| `GET` | `/resolutions` | Verfügbare Videoauflösungen |

## Request-Beispiel

```bash
curl -X POST http://localhost:8014/generate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user-123" \
  -d '{
    "prompt": "Ein Sonnenuntergang über den Bergen",
    "duration": 15,
    "zone": "WORKSPACE",
    "resolution": "1080p"
  }'
```

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `POSTGRES_USER` | `kirobi` | DB-Benutzer |
| `POSTGRES_PASSWORD` | `changeme` | DB-Passwort |
| `POSTGRES_HOST` | `postgres` | DB-Host |
| `POSTGRES_PORT` | `5432` | DB-Port |
| `POSTGRES_DB` | `kirobi` | DB-Name |
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama-Endpunkt |
| `VIDEO_STORAGE_PATH` | `/data/videos` | Speicherpfad für generierte Videos |

## Job-Status

- `pending` — Job erstellt, wartet auf Verarbeitung
- `processing` — Wird gerade generiert
- `completed` — Fertig, `file_path` enthält den Pfad zur Datei
- `failed` — Fehler, `error` enthält die Fehlermeldung

## Verfügbare Auflösungen

- `480p` — Standard Definition (854×480)
- `720p` — High Definition (1280×720)
- `1080p` — Full HD (1920×1080)
- `1440p` — Quad HD (2560×1440)
- `4k` — Ultra HD (3840×2160)
- `square` — Quadratisch 1:1 (1080×1080)
- `portrait` — Hochformat 9:16 (1080×1920)
