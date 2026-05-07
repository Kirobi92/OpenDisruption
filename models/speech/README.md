---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/speech – Sprach-Modelle (STT/TTS)

Konfigurationen und Dokumentation für Sprach-Modelle im Kirobi-Ökosystem: Speech-to-Text (STT) für Spracheingabe und Text-to-Speech (TTS) für Sprachausgabe.

## Zweck

Sprach-Modelle ermöglichen die Voice-First-Interaktion mit Kirobi. STT wandelt Spracheingaben in Text um (für den `voice-agent`), TTS erzeugt natürliche Sprachausgabe aus Text-Antworten.

## Modell-Kategorien

### Speech-to-Text (STT)
| Modell | Anbieter | Einsatz | Anforderung |
|--------|----------|---------|-------------|
| Whisper (large-v3) | OpenAI / lokal via Ollama | Hochqualität, Deutsch | GPU empfohlen |
| Whisper (base/small) | lokal | Schnell, ressourcenschonend | CPU möglich |
| faster-whisper | lokal | Optimierte Inferenz | CPU/GPU |

### Text-to-Speech (TTS)
| Modell | Anbieter | Einsatz | Anforderung |
|--------|----------|---------|-------------|
| Coqui TTS | lokal | Deutsche Stimme, anpassbar | CPU/GPU |
| Piper | lokal | Schnell, leichtgewichtig | CPU |
| ElevenLabs | Cloud (optional) | Hochqualität | API-Key, nur PUBLIC-Daten |

## Modell-Auswahl

- **Alltag / schnelle Antworten:** Whisper small + Piper (lokal, CPU)
- **Hohe Qualität / Interviews:** Whisper large-v3 + Coqui TTS (GPU)
- **Cloud-Fallback:** Nur für PUBLIC-Daten, mit expliziter Genehmigung

## Konfiguration

Der `voice-processing`-Service wird über `docker-compose.yml` und `.env` konfiguriert:

```env
WHISPER_MODEL=base          # base | small | medium | large-v3
TTS_ENGINE=piper            # piper | coqui | elevenlabs
TTS_VOICE=de_DE-thorsten    # Stimmen-ID
```

## Verwandte Verzeichnisse

- `services/voice-processing/` – Voice-Service-Implementierung
- `models/local/` – Lokal laufende Modelle via Ollama
- `prompts/agents/` – System-Prompt für den voice-agent
