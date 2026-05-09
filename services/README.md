# services – Backend-Services und Microservices

**Zone:** WORKSPACE | **Verantwortlich:** kirobi-coder, kirobi-ops

## Zweck
Laufende Anwendungs-Services unter `services/`. Compose-Infrastruktur wie `ollama`, `postgres`, `qdrant`, `open-webui` und `flowise` lebt im Root-Compose, aber nicht in diesem Verzeichnis.

## Service-Übersicht

| Service | Beschreibung | Status |
|---------|-------------|--------|
| `auth/` | JWT-Login, User-/Permissions-Bootstrap, Passwortwechsel | Aktiv |
| `api/` | UI-/client-stabiles REST-Backend für Chat, Uploads, Suche, Dashboard-Tasks | Aktiv |
| `voice-processing/` | STT/TTS und Voice-Session-Endpoints | Aktiv |
| `retrieval/` | Semantische Suche mit Zonen-Enforcement | Aktiv |
| `ingest/` | Ingestion-Pipeline für Inbox/Uploads | Aktiv |
| `embeddings/` | Embedding-Generierung und Store-Endpunkte | Aktiv |
| `model-routing/` | Modellwahl für lokale LLM-Aufgaben | Aktiv |
| `analytics-service/` | Event- und Nutzungsmetriken | Aktiv |
| `image-generation/` | Bildgenerierung | Optionaler Produktpfad |
| `media-processing/` | Medien-Metadaten / Pillow-/mutagen-Workflows | Optionaler Produktpfad |
| `music-generation/` | Musikgenerierung | Optionaler Produktpfad |
| `video-generation/` | Videogenerierung | Optionaler Produktpfad |
| `telegram/` | Externe Telegram-Bot-Schnittstelle | Optional / extern |
| `orchestrator/` | Supervisor- / Backlog-Orchestrierung | Intern |

## Für die unterstützten UI-Surfaces relevant

- `apps/web` hängt primär an `auth` + `api`
- `apps/voice` hängt an `voice-processing` + `api`
- `apps/dashboard` liest Health- und Task-Daten über `api`-Proxies
