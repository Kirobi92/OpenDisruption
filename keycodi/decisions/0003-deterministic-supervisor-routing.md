---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-08
reviewed_by: pending
version: 1.0
---

# ADR 0003 — Deterministisches Agent-Routing im Supervisor

**Datum:** 2026-05-08
**Status:** accepted
**Phase:** 4
**Issue / PR:** pending
**Sven-Sign-off:** optional

---

## Kontext

Der Supervisor delegiert Tasks an spezialisierte Agenten. Für einen autonomen 24/7-Loop darf diese Entscheidung nicht von einer LLM-Antwort, Netzwerkverfügbarkeit oder Prompt-Interpretation abhängen. Routing ist Teil der Sicherheitsarchitektur: Erst werden Zone und Risiko geprüft, dann wird ein Agent ausgewählt, dann wird gehandelt.

Vor dieser Entscheidung konnte Auto-Routing modellabhängig wirken und Fehlerzustände wie `error`, `skipped` oder `deferred` konnten wie erfolgreich abgeschlossene Arbeit behandelt werden. Das gefährdet Reproduzierbarkeit, Auditierbarkeit und Vertrauen in den autonomen Loop.

---

## Optionen

### Option A — LLM-/Ollama-Routing beibehalten

- **Pro:** flexibel bei neuen Formulierungen und unbekannten Task-Typen.
- **Contra:** nicht deterministisch, schwer testbar, anfällig für Prompt-Injection aus Task-Texten.
- **Risiko:** Hoch — gleiche Eingaben können unterschiedliche Agenten erzeugen.

### Option B — Deterministische Keyword- und Zone-Policy im Supervisor

- **Pro:** offline, reproduzierbar, testbar und fail-closed.
- **Pro:** Zonen werden vor Agent-Auswahl geprüft.
- **Contra:** neue Task-Typen brauchen bewusste Erweiterung der Routing-Tabelle.
- **Risiko:** Niedrig bis mittel — konservative Defaults können legitime Tasks blockieren.

### Option C — Externe Routing-Policy als Service

- **Pro:** zentrale Policy für mehrere Runtime-Oberflächen.
- **Contra:** zusätzlicher Dienst, neue Verfügbarkeitsschicht, mehr Ops-Komplexität.
- **Risiko:** Mittel — für P0 zu groß.

---

## Entscheidung

Wir wählen **Option B — deterministische Keyword- und Zone-Policy im Supervisor**.

`route_to_agent()` trifft die Agent-Auswahl lokal anhand von Task-Metadaten, Pfaden, Zone und stabilen Keywords. Für Auto-Routing wird kein LLM, kein Ollama und keine Cloud-API befragt. `PUBLIC` und `WORKSPACE` dürfen an passende Arbeitsagenten geroutet werden; `FAMILY_PRIVATE`, `SACRED` und `QUARANTINE` werden autonom blockiert bzw. an ein Human/Core-Gate deferiert.

Zusätzlich gilt: Ein Routing-Ergebnis ist nur dann erfolgreich, wenn sein Status explizit als Erfolg gilt. `deferred`, `blocked`, `rejected`, `error`, `skipped` oder unbekannte Statuswerte dürfen Tasks nicht als `COMPLETED` markieren.

---

## Konsequenzen

- `services/orchestrator/supervisor.py` enthält eine explizite Routing-Tabelle für `kirobi-coder`, `kirobi-architect`, `kirobi-ops`, `kirobi-frontend`, `kirobi-docs`, `kirobi-reviewer` und sichere lokale Fallbacks.
- `execute_task()` wertet Routing-Status semantisch aus: blockierte Tasks werden `BLOCKED`, Fehler gehen in Retry/Dead-Letter, nur erlaubte Erfolgszustände werden `COMPLETED`.
- Unit-Tests decken Agent-Zuordnung, sensitive Zonen, Quarantäne, Pfad-Zonen und Fehlerstatus ab.
- Die Lösung ist weniger kreativ als LLM-Routing, aber wesentlich sicherer für autonomen Betrieb.

---

## Verworfene Optionen — kurz begründet

- **Option A:** Verworfen, weil Routing Policy ist und nicht probabilistisch sein darf.
- **Option C:** Für P0 verworfen, weil ein eigener Policy-Service mehr Komplexität erzeugt als Nutzen.
- **Silent Fallback:** Verworfen. Unklare oder sensible Tasks werden blockiert/deferiert, nicht geraten.

---

## Referenzen

- `services/orchestrator/supervisor.py`
- `tests/unit/test_supervisor_loop.py`
- `AGENT-DECISION-MATRIX.md`
- `metadata/ZONE-POLICY-MATRIX.md`
- `CLAUDE.md` §2, §3, §7
- `keycodi/decisions/0002-zone-model-fastapi-nextjs-stack.md`
