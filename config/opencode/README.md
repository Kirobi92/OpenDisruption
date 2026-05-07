---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# config/opencode

Konfigurationsdateien fuer opencode-Sitzungen, die als KeyCodi innerhalb von OpenDisruption ausgefuehrt werden. Dieser Ordner enthaelt Prompts und Richtlinien, die opencode beim Start als Kontext erhaelt.

## Zweck

opencode ist ein KI-gestuetztes Coding-Werkzeug, das als Workbench fuer KeyCodi-Missionen genutzt wird. Die hier abgelegten Dateien steuern, mit welcher Identitaet, welchen Richtlinien und welchem Kontext opencode-Sitzungen starten. Sie sind keine Laufzeit-Konfiguration, sondern Prompt-Vorlagen.

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `keycodi-agent.prompt.md` | System-Prompt fuer opencode-Sitzungen im KeyCodi-Modus; definiert Rolle, Delegationsregeln und Sicherheitsrichtlinien |

## Hinweise

- Diese Dateien werden manuell in opencode-Sitzungen eingebunden oder ueber `make keycodi MISSION="..."` referenziert.
- Aenderungen an `keycodi-agent.prompt.md` wirken sich auf alle kuenftigen opencode-Sitzungen aus, die diesen Prompt laden.
- Die eigentliche opencode-Laufzeit-Konfiguration (Agents, Skills, Commands) liegt unter `.opencode/`.
