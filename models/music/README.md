---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/music

Konfiguration und Dokumentation für KI-Musikgenerierungs- und Audioanalyse-Modelle.

## Zweck

Dieser Ordner ist der vorgesehene Ablageort für Modell-Konfigurationen und Auswahlhilfen für Musik- und Audio-KI-Modelle im OpenDisruption-System.

## Status

**Noch nicht aktiv.** Musik-Generierung ist für eine spätere Ausbaustufe geplant — insbesondere im Kontext des Sineo-Creator-Agenten.

## Geplante Modelle

| Modell | Typ | Einsatz |
|--------|-----|---------|
| `MusicGen` (Meta) | Musik-Generierung | Hintergrundmusik, Jingles |
| `AudioCraft` | Audio-Generierung | Sound-Effekte |
| `whisper` | Transkription | Lyrics aus Audio extrahieren |

## Voraussetzungen

Musik-Generierungsmodelle sind rechenintensiv. Lokaler Betrieb erfordert GPU-Profil. Whisper läuft auch auf CPU (langsamer).

## Verwandte Services

- `services/media-processing/` — Aktuell: Audio-Metadaten via mutagen (Port 8012)
- `services/voice-processing/` — Sprachverarbeitung (TTS/STT)
