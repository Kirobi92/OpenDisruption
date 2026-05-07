---
description: Zeigt alle verfügbaren Agenten, ihren Status und ihre Fähigkeiten. Optional: Agent-Name für Details.
agent: keycodi
subtask: true
---

# Agent-Registry: $ARGUMENTS

**1. Registry laden:**
!`python3 -m kirobi_core registry 2>&1`

**2. OpenCode Agents:**
!`ls .opencode/agents/ 2>&1`

**3. Python Agents:**
!`ls agents/ 2>&1`

**4. Agent-Skills:**
!`ls .opencode/skills/ 2>&1`

**Falls Argument angegeben (Agent-Name):**
Zeige Details für diesen spezifischen Agenten:
- Fähigkeiten und Zuständigkeiten
- Zone-Berechtigungen
- Implementierungs-Status (vollständig/Stub)
- Zugehöriger Skill

**Zusammenfassung:**
- Wie viele Agenten sind vollständig implementiert?
- Welche sind nur Stubs?
- Welche OpenCode-Agenten haben Skills?
- Empfehlung: Welcher Agent sollte als nächstes ausgebaut werden?
