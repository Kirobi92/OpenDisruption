---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/unit/agents/hermes

Unit-Tests für den Hermes-Extraktor-Agenten — zuständig für die Ingestion und Klassifizierung von Rohdaten aus `sources/`.
Testet Basis-Funktionalität (Smoke) sowie die korrekte Verweigerung bei Zonen-Verletzungen.

## Wichtige Dateien

- `test_handle_smoke.py` — Smoke-Tests: Hermes startet, verarbeitet valide Eingaben korrekt
- `test_zone_refusal.py` — Hermes verweigert Verarbeitung bei SACRED/FAMILY_PRIVATE-Verletzungen
