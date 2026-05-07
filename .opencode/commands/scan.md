---
description: Scannt das Repository auf Probleme, fehlende Dateien, Zone-Verletzungen und offene Aufgaben.
agent: keycodi
subtask: true
---

# Repository-Scan

Führe einen vollständigen Repository-Scan durch:

**1. kirobi_core Scan:**
!`python3 -m kirobi_core scan 2>&1`

**2. Backlog (Top 10):**
!`python3 -m kirobi_core backlog --limit 10 2>&1`

**3. Doctor Health-Check:**
!`python3 -m kirobi_core doctor 2>&1`

**4. Stub-Services identifizieren:**
!`find services/ apps/ -name "README.md" -exec grep -l "Geplant\|Konzept\|Status.*Geplant" {} \; 2>&1`

**5. Fehlende Tests:**
!`find services/ -name "*.py" | grep -v test | head -20 2>&1`

**Zusammenfassung:**
- Was ist vollständig implementiert?
- Was sind Stubs (nur README)?
- Was sind die Top 5 kritischsten Lücken?
- Empfohlene nächste Mission für KeyCodi?
