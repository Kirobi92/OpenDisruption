---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/unit/agents/openclaw

Unit-Tests für den OpenClaw-Agenten — Web-Scraping und externe Datenerfassung mit Zonen-Sicherheit.
Testet Basis-Funktionalität (Smoke) sowie die korrekte Verweigerung bei Zonen-Verletzungen.

## Wichtige Dateien

- `test_handle_smoke.py` — Smoke-Tests: OpenClaw initialisiert korrekt und verarbeitet valide Requests
- `test_zone_refusal.py` — OpenClaw verweigert Aktionen, die Zonen-Grenzen verletzen würden
