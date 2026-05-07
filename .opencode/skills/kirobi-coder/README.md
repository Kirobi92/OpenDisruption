---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Skill: kirobi-coder

Skill-Definition für den Implementierungs-Spezialisten des OpenDisruption-Ökosystems. Wird von OpenCode geladen, wenn Code geschrieben, getestet oder refaktoriert werden soll.

## Inhalt

- `SKILL.md` — Vollständige Skill-Instruktionen: Stack-Mastery (Python, FastAPI, TypeScript/Next.js), Test-Patterns mit pytest, kirobi_core-Module, Workflow und Sicherheits-Invarianten

## Wann dieser Skill aktiv ist

Der Skill wird geladen bei Aufgaben wie:
- Implementierung neuer FastAPI-Endpunkte
- Schreiben von pytest-Tests
- TypeScript/React-Komponenten für die Family PWA
- Refactoring bestehender Python-Module
- Bugfixes in Services oder kirobi_core

## Sicherheits-Invarianten (Kurzfassung)

- SQL: ausschließlich parametrisierte Queries (`$1, $2, ...`), keine f-Strings
- Secrets: ausschließlich `os.getenv()`, nie hardcoded
- Pfade: Zone-Check vor jeder Datei-Operation
- User-Input: Pydantic-Validierung für alle Eingaben

## Verwandte Ressourcen

- `.opencode/skills/kirobi-architect/SKILL.md` — Architektur-Skill (Vorstufe)
- `tests/unit/` — Bestehende Unit-Tests als Referenz
- `kirobi_core/` — Importierbares stdlib-Modul
