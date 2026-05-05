---
zone: SACRED
type: policy
version: 1.0
---

# Zugriffs-Richtlinie: Sacred Zone

## Zugriffs-Berechtigungen

| Entität | Lesen | Schreiben | Embedding |
|---------|-------|-----------|-----------|
| Sven (Mensch) | ✅ Ja | ✅ Ja | Manuell |
| kirobi-core | ⚠️ HitL-Only | ❌ Nie | ❌ Nie |
| Alle anderen Agenten | ❌ Nie | ❌ Nie | ❌ Nie |

## Human-in-the-Loop Protokoll

Für jeden Agenten-Zugriff auf Sacred-Inhalte:
1. Agent formuliert Anfrage mit vollständiger Begründung
2. Sven erhält Benachrichtigung (Popup oder Sprache)
3. Sven bestätigt oder lehnt ab
4. Aktion wird vollständig geloggt
5. Ergebnis wird nie über Cloud versendet
