---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Voice App — App-Verzeichnis (`apps/voice/src/app`)

Einstiegspunkt der Kirobi Voice PWA: Layout, globale Styles und die Haupt-Seite für die Sprachinteraktion.

## Enthaltene Dateien

| Datei | Zweck |
|-------|-------|
| `layout.tsx` | Root-Layout: HTML-Struktur, Schriftarten, globale CSS-Klassen |
| `globals.css` | Tailwind-Direktiven und animierter Mikrofon-Ring (`mic-ring-active`) |
| `page.tsx` | Hauptseite — vollständige Sprachinteraktions-Logik |

## Was `page.tsx` tut

Die Seite implementiert einen vollständigen Sprach-zu-Sprach-Gesprächskreislauf:

1. **Aufnahme**: Browser-Mikrofon via `MediaRecorder` (bevorzugt `audio/webm;codecs=opus`)
2. **Transkription**: Audio-Blob wird an `POST /voice/transcribe` gesendet → Whisper STT
3. **KI-Antwort**: Transkription wird mit Gesprächsverlauf an `POST /api/chat` gesendet
4. **Sprachausgabe**: Antworttext wird an `POST /voice/synthesize` gesendet → Piper TTS; Wiedergabe erfolgt manuell per Klick (kein Autoplay)

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `NEXT_PUBLIC_VOICE_SERVICE_URL` | `/voice` | Basis-URL des `voice-processing`-Service (Port 8001) |
| `NEXT_PUBLIC_API_URL` | `/api` | Basis-URL des `api`-Service (Port 8003) |

## Zustände

- `idle` — Bereit, wartet auf Mikrofon-Klick
- `recording` — Aufnahme läuft, pulsierender roter Ring
- `processing` — Transkription/KI/TTS werden verarbeitet, Spinner aktiv

## Bekannte Einschränkungen

- Mikrofon-Berechtigung muss vom Browser erteilt werden; Fehler werden im UI angezeigt
- TTS-Antwort wird nicht automatisch abgespielt (Browser-Autoplay-Richtlinien)
- Gesprächsverlauf wird nur im React-State gehalten — kein persistentes Speichern
