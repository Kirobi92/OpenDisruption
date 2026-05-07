---
description: Architektur-Entscheidung für ein neues Feature oder Problem. Erstellt ADR mit Optionen, Entscheidung und Implementierungs-Plan.
agent: kirobi-architect
subtask: true
---

Erstelle eine Architektur-Entscheidung (ADR) für: $ARGUMENTS

**Format:**

## ADR: $ARGUMENTS

### Kontext
Was ist die Situation? Was ist das Problem?

### Optionen
1. Option A — [Kurzbeschreibung]
   - Pro: ...
   - Contra: ...

2. Option B — [Kurzbeschreibung]
   - Pro: ...
   - Contra: ...

### Entscheidung
[Gewählte Option und Begründung]

### Konsequenzen
- Positive Auswirkungen
- Negative Auswirkungen / Risiken
- Offene Fragen

### Implementierungs-Plan
Aufgaben für kirobi-coder, kirobi-ops, kirobi-frontend (je nach Scope)

---

Berücksichtige dabei:
- Das Zone-Modell (SACRED → PUBLIC)
- Den bestehenden Stack (FastAPI, asyncpg, Next.js 15, Docker Compose)
- Das Prinzip: Dateisystem ist System of Record
- Idempotenz und Rebuildfähigkeit aller Services
