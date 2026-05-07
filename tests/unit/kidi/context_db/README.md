---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/unit/kidi/context_db

Unit-Tests für die KiDi-Kontext-Datenbank — das Herzstück der Zonen-sicheren Wissensspeicherung.
Prüft Zonen-Durchsetzung, Egress-Guards (kein FAMILY_PRIVATE/SACRED nach außen), Schlüsselverwaltung und Merge-Konflikte.

## Wichtige Dateien

- `test_zone_enforcement.py` — Zonen-Zugriffsregeln und Berechtigungsprüfungen
- `test_egress_guard.py` — Verhindert unerlaubten Datenabfluss aus geschützten Zonen
- `test_keys.py` — Schlüsselverwaltung und Namenskonventionen
- `test_merge.py` — Konfliktauflösung beim Zusammenführen von Kontext-Einträgen
