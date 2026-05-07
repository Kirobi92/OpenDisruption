---
description: Führt alle Tests aus und zeigt Coverage. Optional: spezifisches Modul oder Test-Pattern als Argument.
agent: kirobi-coder
subtask: true
---

# Test-Run: $ARGUMENTS

Führe Tests aus und analysiere Ergebnisse:

**1. Unit-Tests:**
!`python3 -m pytest tests/unit -q 2>&1`

**2. Falls Argument angegeben (z.B. "zones" oder "test_audit.py"):**
!`python3 -m pytest tests/unit -k "$ARGUMENTS" -v 2>&1`

**3. Compose-Validierung:**
!`docker compose config --quiet && echo "Compose: ✅ OK"`

**4. Analyse:**
- Wie viele Tests passed/failed/skipped?
- Welche Tests sind neu fehlgeschlagen?
- Gibt es Muster in den Fehlern?
- Was sind die nächsten Schritte?

Falls Tests fehlschlagen: Analysiere die Fehler und schlage konkrete Fixes vor.
