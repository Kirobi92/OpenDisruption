---
zone: WORKSPACE
created_by: kirobi-coder
created_at: 2026-05-08
version: 1.0.0
---

# Kirobi Music Generation Service

**Port:** 8013  
**Zone:** WORKSPACE  
**Zweck:** Asynchrone KI-Musikgenerierung via Ollama (Text-to-Music-Prompts)

## Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| `GET` | `/health` | Health-Check (DB + Ollama) |
| `POST` | `/generate` | Neuen Musik-Job erstellen (async) |
| `GET` | `/jobs/{job_id}` | Job-Status abfragen |
| `GET` | `/jobs` | Alle Jobs des Users (Header: `X-User-Id`) |
| `GET` | `/styles` | Verfügbare Musikstile |

## Request-Beispiel

```bash
curl -X POST http://localhost:8013/generate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user-123" \
  -d '{
    "prompt": "Ruhige Ambient-Musik für Meditation",
    "duration": 60,
    "zone": "WORKSPACE",
    "style": "ambient"
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
| `MUSIC_STORAGE_PATH` | `/data/music` | Speicherpfad für generierte Musik |

## Job-Status

- `pending` — Job erstellt, wartet auf Verarbeitung
- `processing` — Wird gerade generiert
- `completed` — Fertig, `file_path` enthält den Pfad zur Datei
- `failed` — Fehler, `error` enthält die Fehlermeldung

## Verfügbare Stile

- `ambient` — Ruhige, atmosphärische Klänge
- `electronic` — Elektronische Beats und Synthesizer
- `classical` — Klassische Orchestermusik
- `jazz` — Improvisierter Jazz
- `lofi` — Entspannte Lo-Fi Hip-Hop Beats
- `cinematic` — Filmmusik und epische Soundtracks
- `nature` — Naturgeräusche und Klanglandschaften
- `meditation` — Meditative Klänge und Binaural Beats
