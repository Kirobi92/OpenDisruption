---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/vision

Konfiguration und Dokumentation für multimodale Vision-Modelle (Bild-Verständnis, OCR, visuelle Analyse).

## Zweck

Vision-Modelle ermöglichen es Agenten, Bilder zu analysieren, Text aus Bildern zu extrahieren (OCR) und visuelle Inhalte zu beschreiben. Dieser Ordner dokumentiert verfügbare Modelle und deren Einsatzgebiete.

## Aktuell verwendete Modelle

| Modell | Typ | Einsatz | Profil |
|--------|-----|---------|--------|
| `llava:7b` | Vision-LLM | Bild-Beschreibung, visuelle Q&A | CPU + GPU |

## Modell-Auswahl

- **llava:7b** — Kompaktes Vision-Modell; versteht Bilder und beantwortet Fragen dazu. Läuft auf CPU-Profil, aber langsam.
- **llava:34b** — Höhere Qualität; erfordert GPU mit ≥ 20 GB VRAM.
- **moondream** — Sehr kleines Vision-Modell für einfache Bild-Klassifikation auf schwacher Hardware.

## Typische Aufgaben

- Bild-Inhalte beschreiben (für Accessibility oder Suche)
- Dokument-Scans analysieren
- Screenshots verstehen (z. B. für den Supervisor-Agenten)
- Visuelle Qualitätsprüfung generierter Bilder

## Verwandte Services

- `services/image-generation/` — Nutzt llava als Fallback-Modell (Port 8011)
- `services/media-processing/` — Bild-Resize und Format-Konvertierung (Port 8012)
