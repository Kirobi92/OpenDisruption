---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# services/music-generation – Musik-Generierungs-Service

Geplanter Service zur KI-gestützten Musik-Generierung im Kirobi-Ökosystem. Ermöglicht die Erstellung von Hintergrundmusik, Soundscapes und kreativen Audio-Kompositionen – primär für Sineo (Creator-Workflow) und familiäre Erlebnisse.

## Zweck

Musik ist ein zentrales Ausdrucksmittel für Sineo und die Familie Darusi. Dieser Service soll lokale Musik-Generierung ermöglichen, ohne Kreativ-Daten an Cloud-Dienste zu senden.

## Status

**Konzept** – Noch nicht implementiert. Technologie-Evaluation läuft.

## Geplante Technologie

| Modell / Tool | Anbieter | Stärken | Ressourcen |
|---------------|----------|---------|-----------|
| MusicGen (small/medium) | Meta / lokal | Text-to-Music, offen | ~4–8 GB VRAM |
| AudioCraft | Meta / lokal | Soundscapes, Effekte | ~4 GB VRAM |
| Suno API | Cloud (optional) | Hochqualität, Gesang | Nur PUBLIC-Daten |
| Udio API | Cloud (optional) | Stilvielfalt | Nur PUBLIC-Daten |

## Geplante API

```
POST /generate
  body: { prompt: str, duration_seconds: int, style: str }
  response: { audio_url: str, job_id: str }

GET /status/{job_id}
  response: { status: "pending" | "done" | "error", audio_url?: str }
```

## Zonen-Hinweis

Generierte Musik auf Basis familiärer Prompts oder persönlicher Texte ist `FAMILY_PRIVATE`. Rein instrumentale, nicht-personenbezogene Generierungen können `WORKSPACE` sein.

## Verwandte Verzeichnisse

- `models/music/` – Musik-Modell-Konfigurationen
- `models/speech/` – TTS-Modelle (Audio-Ausgabe allgemein)
- `services/voice-processing/` – Voice-Service als Referenz-Implementierung
