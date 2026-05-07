---
description: Deployment-Check und Stack-Start. Validiert Config, prüft .env, startet Services.
agent: kirobi-ops
subtask: true
---

Führe einen vollständigen Deployment-Check durch $ARGUMENTS:

**1. Voraussetzungen prüfen:**
!`docker compose config --quiet && echo "Compose: OK"`
!`bash infra/scripts/validate-env.sh 2>&1 | tail -10`

**2. Git-Status:**
!`git status --short`
!`git log --oneline -5`

**3. Service-Status:**
!`docker compose ps 2>&1 | head -20`

**4. Empfehlung:**
- Sind alle Voraussetzungen erfüllt?
- Welche Services müssen neu gebaut werden? (`docker compose build <service>`)
- Was sind die nächsten Schritte zum erfolgreichen Deployment?

Falls Argument angegeben (z.B. "telegram"): fokussiere auf diesen Service.

**Wichtig:** Führe `docker compose up` NICHT selbst aus — sage Sven den Befehl.
