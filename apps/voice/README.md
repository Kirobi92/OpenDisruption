---
zone: WORKSPACE
created_by: kirobi-ops
created_at: 2026-05-08
reviewed_by: pending
version: 1.0
---

# Kirobi Voice — apps/voice

Eigenständige Next.js 15 App für das Kirobi Voice-Interface.  
Läuft auf **Port 3004** und kommuniziert mit dem `voice-processing`-Service (Port 8001) sowie dem `api`-Service (Port 8003).

## Features

- 🎙️ **Mikrofon-Button** — Aufnahme starten/stoppen per Klick
- 📝 **Transkription** — Audio wird via `POST /voice/transcribe` an den `voice-processing`-Service gesendet (Whisper large-v3)
- 🤖 **KI-Antwort** — Transkription wird an `POST /api/chat` weitergeleitet; Gesprächshistorie wird im Client-State gehalten
- 🔊 **Sprachausgabe** — Antwort kann via `POST /voice/synthesize` vorgelesen werden
- 🔄 **Gespräch zurücksetzen** — Löscht History und UI-State

## Entwicklung

```bash
cd apps/voice
npm install
npm run dev        # http://localhost:3004
```

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `NEXT_PUBLIC_VOICE_SERVICE_URL` | `/voice` | URL zum voice-processing Service (via Caddy) |
| `NEXT_PUBLIC_API_URL` | `/api` | URL zum API Service (via Caddy) |

Im Docker-Compose-Betrieb werden alle Anfragen über Caddy geroutet — keine direkten Service-URLs nötig.

## Architektur

```
Browser (Port 3004)
  └─► Caddy (:80/:443)
        ├─► /voice/* → voice-processing:8001
        └─► /api/*   → api:8000
```

## Technologie-Stack

- Next.js 15 (App Router, `output: standalone`)
- React 18 + TypeScript strict
- Tailwind CSS 3 (Dark Mode, kirobi-Farbpalette)
- Keine externen State-Management-Bibliotheken — reines React `useState`/`useRef`
- `MediaRecorder` API für Browser-seitige Aufnahme (WebM/Opus)
