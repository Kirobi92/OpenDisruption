---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/image

Konfiguration und Dokumentation für KI-Bildgenerierungs-Modelle im OpenDisruption-System.

## Zweck

Dieser Ordner enthält Modell-Konfigurationen, Benchmarks und Auswahlhilfen für Bildgenerierungs-Modelle, die vom `services/image-generation`-Service genutzt werden.

## Aktuell verwendete Modelle

| Modell | Typ | Einsatz | Hinweis |
|--------|-----|---------|---------|
| `llava:7b` | Vision-LLM | Standard (Ollama) | Generiert Text-Beschreibungen, kein echtes Bild-Rendering |

## Modell-Auswahl

- **llava:7b** — Standardmodell; geringer GPU-Bedarf, läuft auf CPU-Profil als Fallback
- **stable-diffusion** — Für echte Pixel-Ausgabe nötig; erfordert separates Ollama-Backend oder externe Integration (aktuell nicht aktiv)

## Bekannte Einschränkungen

`llava` ist ein Vision-Modell (Bild-Analyse), kein Diffusion-Modell. Der `image-generation`-Service speichert bei llava einen Platzhalter-PNG mit dem generierten Text. Für echte Bildgenerierung ist ein Diffusion-Modell (z. B. `stable-diffusion-webui`) erforderlich.

## Verwandte Services

- `services/image-generation/` — FastAPI-Service auf Port 8011
