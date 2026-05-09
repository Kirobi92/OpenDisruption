# services/voice-processing/

**Verantwortlich:** kirobi-coder  
**Status:** Aktiv

## Zweck
Sprach-Verarbeitungs-Service: STT (Speech-to-Text) und TTS (Text-to-Speech).

## Wichtige Endpunkte

| Methode | Pfad |
|---|---|
| `GET` | `/health`, `/audio/{filename}`, `/conversation/status/{session_id}`, `/models/info` |
| `POST` | `/stt/transcribe`, `/tts/synthesize`, `/conversation/start`, `/conversation/end/{session_id}` |

## Verwendet von

- `apps/voice` als primäre Sprach-Oberfläche
- optionalen Voice-/Interview-Flows im Stack

## Technologie

- Whisper / faster-whisper für STT
- Piper/TTS-Flow für Sprachausgabe
- Python + FastAPI
