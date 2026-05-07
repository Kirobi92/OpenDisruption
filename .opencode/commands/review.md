---
description: Vollständiges Code-Review mit Security-Audit durch kirobi-reviewer. Optional: Datei oder Verzeichnis als Argument.
agent: kirobi-reviewer
subtask: true
---

Führe ein vollständiges Code-Review durch für: $ARGUMENTS

Falls kein Argument angegeben: Review der zuletzt geänderten Dateien:
!`git diff --name-only HEAD~1 HEAD 2>/dev/null || git status --short`

**Review-Scope:**
1. Security-Findings (SQL-Injection, Auth-Bypasses, Credential-Leaks, Zone-Verletzungen)
2. Code-Qualität (Fehler-Handling, Typisierung, Testbarkeit)
3. Konformität mit AGENTS.md Style-Guide
4. Fehlende Tests für kritische Pfade

Nutze das Standard-Output-Format aus deiner Agent-Konfiguration.
Priorisiere: KRITISCH > WARNUNG > INFO
