---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# agents/openclaw

OpenClaw-Agent — spezialisiert auf Web-Scraping, externe Datenerfassung und Quarantäne-konforme Ingestion.
Alle gesammelten Daten landen zunächst in `sources/inbox/` (QUARANTINE) und müssen von Hermes geprüft werden.

## Wichtige Dateien

- `agent.py` — Haupt-Agenten-Logik: Scraping, Zonen-Prüfung, Quarantäne-Ablage
- `__init__.py` — Python-Paket-Marker
- `Dockerfile` — Container-Definition für isolierte Ausführung
