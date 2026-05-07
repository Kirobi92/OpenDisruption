---
description: System-Status: Health-Check, offene Tasks, kritische Lücken und nächste empfohlene Schritte.
agent: keycodi
subtask: true
---

Führe einen vollständigen System-Status-Check durch:

1. **kirobi_core Health**:
   !`python3 -m kirobi_core doctor 2>&1 | head -30`

2. **Unit-Tests**:
   !`python3 -m pytest tests/unit -q 2>&1 | tail -5`

3. **Compose-Validierung**:
   !`docker compose config --quiet 2>&1 && echo "Compose: OK"`

4. **Repo-Scan** (Stubs und fehlende Files):
   !`python3 -m kirobi_core backlog --limit 5 2>&1`

5. **Git-Status**:
   !`git status --short | head -20`

Fasse zusammen:
- Was ist gesund?
- Was ist kaputt oder unvollständig?
- Was sind die **Top 3 nächsten Aktionen** für KeyCodi?
