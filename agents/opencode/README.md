---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# agents/opencode

OpenCode-Agent — Brücke zwischen KeyCodi-Orchestrierung und der OpenCode-Workbench (Port 4096).
Empfängt Missions-Aufträge von KeyCodi und delegiert sie an die OpenCode-UI oder führt sie direkt aus.

## Wichtige Dateien

- `agent.py` — Haupt-Agenten-Logik: Mission-Empfang, OpenCode-Handoff, Ergebnis-Rückgabe
- `__init__.py` — Python-Paket-Marker
- `Dockerfile` — Container-Definition für isolierte Ausführung
