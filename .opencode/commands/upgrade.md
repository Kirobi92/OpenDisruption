---
description: Führt einen vollständigen System-Upgrade durch — analysiert Lücken, erstellt Plan, delegiert Implementierung.
agent: keycodi
---

# System-Upgrade: $ARGUMENTS

Lade den Skill `keycodi-orchestrator` und führe einen vollständigen Upgrade-Zyklus durch:

**Phase 1 — Vollständige Analyse:**
!`python3 -m kirobi_core doctor 2>&1`
!`python3 -m kirobi_core backlog --limit 20 2>&1`
!`python3 -m pytest tests/unit -q 2>&1 | tail -5`

**Phase 2 — Lücken-Analyse:**
Identifiziere:
1. Stub-Services (nur README, kein Code)
2. Fehlende Tests
3. Fehlende Skills/Commands
4. Deaktivierte MCP-Server
5. Unvollständige Agent-Definitionen

**Phase 3 — Upgrade-Plan:**
Erstelle priorisierten Plan:
- P0: Blockiert MVP (sofort)
- P1: Wichtig (diese Woche)
- P2: Zukunft (nächster Sprint)

**Phase 4 — Ausführung:**
Falls Argument angegeben: Führe diesen spezifischen Upgrade-Schritt aus.
Sonst: Führe P0-Items autonom aus.

**Phase 5 — Validierung:**
!`python3 -m pytest tests/unit -q 2>&1`
!`docker compose config --quiet 2>&1`

**Bericht:** Was wurde upgraded, was bleibt offen.
