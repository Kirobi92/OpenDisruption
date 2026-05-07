---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/video

Konfiguration und Dokumentation für KI-Videogenerierungs- und Videoanalyse-Modelle.

## Zweck

Dieser Ordner ist der vorgesehene Ablageort für Modell-Konfigurationen, Benchmarks und Auswahlhilfen für Video-bezogene KI-Modelle im OpenDisruption-System.

## Status

**Noch nicht aktiv.** Video-Verarbeitung ist für eine spätere Ausbaustufe geplant.

## Geplante Modelle

| Modell | Typ | Einsatz |
|--------|-----|---------|
| `llava:34b` | Video-Frame-Analyse | Beschreibung von Video-Inhalten |
| `whisper` | Audio-Transkription | Untertitel aus Video-Audio |

## Voraussetzungen

Video-Modelle erfordern erhebliche GPU-Ressourcen (≥ 16 GB VRAM für 34b-Modelle). Auf CPU-Profil nicht sinnvoll einsetzbar.

## Verwandte Services

- `services/media-processing/` — Aktuell: Bild-Resize und Audio-Metadaten (Port 8012)
