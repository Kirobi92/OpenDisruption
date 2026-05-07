---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# .opencode

Konfigurationsverzeichnis fuer die opencode-Laufzeit im OpenDisruption-Oekosystem. Enthaelt Agent-Definitionen, Slash-Commands, Skills und Plugin-Konfiguration.

## Zweck

opencode ist ein KI-gestuetztes Coding-Werkzeug, das als Workbench fuer KeyCodi-Missionen genutzt wird. Dieses Verzeichnis steuert vollstaendig, welche Agenten, Befehle und Faehigkeiten in opencode-Sitzungen verfuegbar sind. Es ist die Laufzeit-Konfiguration; die Prompt-Vorlagen liegen unter `config/opencode/`.

## Struktur

| Ordner/Datei | Beschreibung |
|--------------|-------------|
| `agents/` | Agent-Definitionen (Modell, Berechtigungen, System-Prompt) fuer alle 7 Kirobi-Spezialisten |
| `commands/` | Slash-Commands (`/mission`, `/scan`, `/backlog`, `/deploy`, `/review`, u.a.) |
| `skills/` | Skill-Bibliothek mit detaillierten Workflow-Instruktionen pro Agent-Rolle |
| `plugins/` | opencode-Plugin-Konfiguration |
| `package.json` | NPM-Abhaengigkeiten (aktuell: `@opencode-ai/plugin`) |
| `.gitignore` | Schliesst `node_modules/` und generierte Dateien aus |

## Registrierte Skills

| Skill | Beschreibung |
|-------|-------------|
| `keycodi-orchestrator` | Vollstaendiges Workflow-Wissen fuer den Master-Orchestrator |
| `kirobi-architect` | Architektur-Entscheidungen und System-Design |
| `kirobi-coder` | Implementierungs-Richtlinien (Python, TypeScript) |
| `kirobi-docs` | Dokumentations-Standards und Schreibregeln |
| `kirobi-frontend` | Next.js/React/TailwindCSS-Konventionen |
| `kirobi-ops` | Docker Compose, Infrastruktur, Deployment |
| `kirobi-reviewer` | Security-Audit und Code-Review-Prozesse |

## Wichtige Slash-Commands

`/mission`, `/scan`, `/backlog`, `/deploy`, `/review`, `/test`, `/refactor`, `/status`, `/agents`, `/kidi`, `/architect`, `/autonomous`, `/upgrade`

## Hinweise

- `node_modules/` wird nicht committet (`.gitignore`).
- Aenderungen an Agent-Definitionen oder Skills wirken sofort in der naechsten opencode-Sitzung.
- Die kanonische, verifiziete Skill-Quelle ist `.opencode/skills/keycodi-orchestrator/SKILL.md` (laut `AGENTS.md`).
