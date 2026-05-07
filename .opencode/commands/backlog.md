---
description: Zeigt den aktuellen Backlog mit priorisierten Aufgaben. Optional: Limit als Argument (default: 10).
agent: keycodi
subtask: true
---

# Backlog: $ARGUMENTS

**1. Priorisierter Backlog:**
!`python3 -m kirobi_core backlog --limit ${ARGUMENTS:-10} 2>&1`

**2. Git-Status (uncommitted changes):**
!`git status --short 2>&1 | head -20`

**3. Letzte Commits:**
!`git log --oneline -10 2>&1`

**Analyse:**
- Welche Tasks haben höchste Priorität?
- Welche Tasks kann KeyCodi autonom bearbeiten (WORKSPACE-Zone)?
- Welche Tasks brauchen Sven's Approval?
- Empfehlung: Was als nächstes angehen?
