---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# .opencode/agents

Agent-Definitionen fuer opencode. Jede Markdown-Datei beschreibt einen spezialisierten Agenten mit Identitaet, Modell-Konfiguration, Berechtigungen und System-Prompt.

## Zweck

opencode laedt diese Dateien beim Start und stellt die definierten Agenten als auswaehlbare Personas bereit. Die Konfiguration steuert Modell, Temperatur, Reasoning-Tiefe und erlaubte Tool-Berechtigungen pro Agent.

## Registrierte Agenten

| Datei | Agent | Rolle |
|-------|-------|-------|
| `keycodi.md` | KeyCodi | Master-Code-Orchestrator; plant, delegiert und integriert |
| `kirobi-architect.md` | kirobi-architect | System-Design, Architektur-Entscheidungen, API-Contracts |
| `kirobi-coder.md` | kirobi-coder | Implementierung, Tests, Bugfixes (Python, TypeScript) |
| `kirobi-docs.md` | kirobi-docs | Dokumentation, README-Dateien, Kommentare (Deutsch) |
| `kirobi-frontend.md` | kirobi-frontend | Next.js, React, TailwindCSS, PWA |
| `kirobi-ops.md` | kirobi-ops | Docker Compose, Shell-Scripts, CI/CD, Infrastruktur |
| `kirobi-reviewer.md` | kirobi-reviewer | Security-Audit, Code-Review, Qualitaetssicherung |

## Dateiformat

Jede Agent-Datei enthaelt YAML-Frontmatter mit:
- `description` — Kurzbeschreibung der Rolle
- `mode` — `primary` oder `assistant`
- `model` — Zu verwendendes Modell
- `temperature` — Kreativitaets-Parameter
- `permission` — Erlaubte Tools (edit, bash, read, glob, grep, task, webfetch, skill)

Gefolgt von einem optionalen Markdown-System-Prompt.
