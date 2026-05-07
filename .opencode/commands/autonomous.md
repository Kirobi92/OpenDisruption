---
description: Führt einen autonomen Arbeits-Zyklus aus — analysiert Backlog, wählt sichere Task, implementiert, testet.
agent: keycodi
---

# Autonomer Arbeits-Zyklus: $ARGUMENTS

Lade den Skill `keycodi-orchestrator` und führe einen vollständigen autonomen Zyklus durch:

**Phase 1 — Analyse:**
!`python3 -m kirobi_core autonomous-once 2>&1`
!`python3 -m kirobi_core backlog --limit 5 2>&1`

**Phase 2 — Task-Auswahl:**
Wähle den höchst-priorisierten Task der:
- Zone WORKSPACE oder PUBLIC ist
- Autonom bearbeitbar ist (kein Human-Gate nötig)
- Klar definiert und abgrenzbar ist

Falls Argument angegeben: Bearbeite diesen spezifischen Task.

**Phase 3 — Implementierung:**
Delegiere an den passenden Spezialisten:
- Code → @kirobi-coder
- Architektur → @kirobi-architect  
- Infra → @kirobi-ops
- Frontend → @kirobi-frontend
- Docs → @kirobi-docs

**Phase 4 — Validierung:**
!`python3 -m pytest tests/unit -q 2>&1`
!`docker compose config --quiet 2>&1`

**Phase 5 — Bericht:**
- Was wurde implementiert?
- Welche Tests wurden hinzugefügt?
- Was bleibt offen?
- Nächster empfohlener autonomer Schritt?
