---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: 1.0
---

# Learning 0002 — Phase 2: Basisklasse vor Agenten, nicht umgekehrt

**Datum:** 2026-05-07
**Phase:** 2
**Issue / PR:** #TBD (Phase 2 PR)
**Autor:** keycodi
**Schweregrad:** info
**Zone-Auswirkung:** WORKSPACE

---

## Symptom

Phase 2 sollte 4 unabhängige Agenten-Skelette liefern. Die Frage war: wie
verhindert man Duplikation der Zone-Validierungs-Logik in jedem Agenten?

## Erwartung vs. Realität

- **Erwartet:** Jeder Agent implementiert seine eigene Zone-Prüfung — 4x
  duplizierter Code, 4x unterschiedliche Fehlermeldungen.
- **Tatsächlich:** `BaseAgent.run()` übernimmt Zone-Validierung, Approval-Check,
  ContextDB-Schreiben und Audit-Logging zentral. Jeder Agent implementiert
  nur `handle()` — ca. 40 Zeilen statt 150.

## Hypothesen

1. Dependency Injection (`context_db`-Parameter) hält Tests einfach —
   kein Mock nötig wenn `None` übergeben wird.
2. `frozenset` für `allowed_input_zones` / `allowed_output_zones` ist
   deklarativ und testbar ohne Instanz.
3. Abstract `handle()` erzwingt Implementierung beim Compile-Time — keine
   Runtime-Überraschungen.

## Versuche

| Versuch | Maßnahme | Ergebnis |
|---------|----------|----------|
| 1 | `BaseAgent.run()` mit Template-Method-Pattern | ✅ 52 Tests grün, 0.16s |
| 2 | Remote-MCP-Server aktiviert | ❌ Test-Policy verletzt — sofort zurückgesetzt |

## Ergebnis

Template-Method-Pattern in `BaseAgent.run()` + `@abstractmethod handle()` ist
das richtige Muster für diesen Agenten-Stack. Zone-Enforcement ist einmal
implementiert, überall erzwungen.

Der Versuch Remote-MCP-Server (`context7`, `gh-grep`) zu aktivieren scheiterte
an einem bestehenden Security-Test (`test_keycodi.py::test_opencode_config_defaults_to_local_first_keycodi`).
Richtige Entscheidung: Policy-Test nicht deaktivieren, stattdessen nur den
lokalen `kirobi-supervisor` MCP aktivieren.

## Folgewirkung

- Tests hinzugefügt: ja — 52 Agenten-Tests in `tests/unit/agents/`
- Doku aktualisiert: ja — `MILESTONES.md` Phase 2, `ROADMAP.md` Status
- ADR nötig: nein (Standard Template-Method)
- Roadmap-Item beeinflusst: Phase 2 ✅, Phase 3 kann starten

## Lehre für KeyCodi

Security-Tests nie deaktivieren um Features zu aktivieren — wenn ein Test
eine Policy schützt, ist die Policy wichtiger als die neue Funktion.
Remote-MCP-Server bleiben disabled bis Sven explizit genehmigt.
