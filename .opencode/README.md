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
| `agents/` | Agent-Definitionen (Modell, Berechtigungen, System-Prompt) fuer Kirobi-Spezialisten plus generische Review-/Test-/Security-Personas |
| `commands/` | Slash-Commands (`/mission`, `/scan`, `/backlog`, `/deploy`, `/review`, u.a.) |
| `skills/` | Skill-Bibliothek mit repo-spezifischen KeyCodi/Kirobi-Skills plus importiertem Lifecycle-Pack aus `agent-skills` |
| `references/` | Gemeinsame Checklisten und Referenzen fuer die importierten Agent-Skills |
| `plugins/` | opencode-Plugin-Konfiguration |
| `package.json` | NPM-Abhaengigkeiten (aktuell: `@opencode-ai/plugin`) |
| `LICENSE.agent-skills` | MIT-Lizenz des eingebundenen Upstream-Skill-Packs |
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

## Zusaetzlich importierte Lifecycle-Skills

Der MIT-lizenzierte Pack `addyosmani/agent-skills` ist jetzt ebenfalls unter `.opencode/skills/`
eingebunden. Damit stehen unter anderem diese generischen Entwicklungs-Skills zur Verfuegung:

- Define: `using-agent-skills`, `idea-refine`, `spec-driven-development`
- Plan: `planning-and-task-breakdown`
- Build: `incremental-implementation`, `context-engineering`, `source-driven-development`, `doubt-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`
- Verify: `test-driven-development`, `browser-testing-with-devtools`, `debugging-and-error-recovery`
- Review: `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`
- Ship: `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `shipping-and-launch`

## Wichtige Slash-Commands

`/mission`, `/scan`, `/backlog`, `/deploy`, `/review`, `/test`, `/refactor`, `/status`, `/agents`, `/kidi`, `/architect`, `/autonomous`, `/upgrade`

## Hinweise

- `node_modules/` wird nicht committet (`.gitignore`).
- Aenderungen an Agent-Definitionen oder Skills wirken sofort in der naechsten opencode-Sitzung.
- Die kanonische, verifiziete Repo-spezifische Skill-Quelle ist `.opencode/skills/keycodi-orchestrator/SKILL.md` (laut `AGENTS.md`).
- Die importierten Lifecycle-Skills ergaenzen die lokalen Repo-Policies, ersetzen sie aber nicht.
