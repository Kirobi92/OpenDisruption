---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/avatar – Avatar-Modelle

Konfigurationen und Dokumentation für Avatar-Modelle im Kirobi-Ökosystem. Avatar-Modelle erzeugen visuelle Repräsentationen von Kirobi-Agenten oder Familienmitgliedern für die PWA-Oberfläche und zukünftige Video-Interaktionen.

## Zweck

Ein Avatar verleiht einem Agenten ein Gesicht. Für Kirobi bedeutet das: konsistente visuelle Identitäten für die Agenten (z. B. Kirobi-Core, Samira-Heart, Sineo-Creator), die in der Family PWA angezeigt werden und das Vertrauen in die Mensch-KI-Interaktion stärken.

## Modell-Kategorien

### Statische Avatare
Vorberechnete Bilder oder SVG-Illustrationen – kein Modell erforderlich, nur Assets.

### Dynamische Avatare (geplant)
| Modell | Anbieter | Einsatz | Status |
|--------|----------|---------|--------|
| SadTalker | lokal | Lippensynchronisation zu TTS-Audio | Konzept |
| DID / HeyGen | Cloud (optional) | Hochqualität, realistisch | Nur PUBLIC-Daten |
| Stable Diffusion (SDXL) | lokal | Konsistente Stil-Avatare | Konzept |

## Einsatzbereiche

- **PWA-Profil-Icons** – Statische Avatare für jeden Agenten
- **Voice-Antworten** – Animierter Avatar synchron zur TTS-Ausgabe (geplant)
- **Onboarding** – Freundliches Gesicht beim Setup-Wizard

## Zonen-Hinweis

Avatar-Modelle für Familienmitglieder (Fotos, Stimmen) sind `FAMILY_PRIVATE` und dürfen **niemals** an Cloud-Dienste übertragen werden. Nur stilisierte, nicht-identifizierbare Avatare können `WORKSPACE` sein.

## Verwandte Verzeichnisse

- `models/image/` – Bild-Generierungs-Modelle (Stable Diffusion)
- `models/video/` – Video-Modelle für animierte Avatare
- `models/speech/` – TTS-Modelle für Lippensynchronisation
- `apps/web/public/` – Statische Avatar-Assets der PWA
