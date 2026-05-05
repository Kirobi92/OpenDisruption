---
zone: WORKSPACE
type: wissen
version: 1.0
---

# Sprache, Geste und Emotion: Multi-Modal-Interaktion

## Vision: Vollständige Mensch-KI-Interaktion

Kirobi versteht nicht nur Text, sondern auch Tonalität, Kontext und — in Zukunft — visuelle Signale.

## Aktuelle Modalitäten

### Text
- Direkte Eingabe über Open-WebUI
- API-Aufrufe über Backend

### Sprache (geplant)
- Spracheingabe via Whisper
- Sprachausgabe via Kokoro-TTS
- Wake-Word via Rhasspy

### Emotion (geplant)
- Tonalitäts-Erkennung in Sprache
- Kontext-sensitives Routing basierend auf erkannter Emotion

## Design-Prinzipien

1. **Einwilligung zuerst:** Emotion-Erkennung nur mit explizitem Consent
2. **Transparent:** Agent informiert wenn Ton-Analyse aktiv
3. **Lokal:** Alle Analyse-Modelle laufen on-device
