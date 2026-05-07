---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# .opencode/skills/kirobi-ops

OpenCode-Skill fuer den kirobi-ops-Agenten. Enthaelt die vollstaendigen Skill-Instruktionen fuer DevOps-Aufgaben im OpenDisruption-Oekosystem: Docker Compose, Shell-Scripts, CI/CD, Infrastruktur-Konfiguration und Service-Deployment.

## Zweck

Wenn ein opencode-Agent den kirobi-ops-Skill laedt, erhaelt er detaillierte Anweisungen zum Service-Graphen, zu Compose-Profilen, Healthchecks, Backup-Prozeduren und Sicherheits-Richtlinien fuer Infrastruktur-Aenderungen.

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `SKILL.md` | Vollstaendige Skill-Instruktionen: Service-Ports, Compose-Profile, Deployment-Regeln, Sicherheitshinweise und bekannte Fallstricke |

## Verwendung

Der Skill wird automatisch geladen, wenn ein opencode-Agent eine Aufgabe mit Infrastruktur-Bezug erkennt, oder explizit ueber das `skill`-Tool:

```
skill("kirobi-ops")
```

## Abgedeckte Themen in SKILL.md

- Vollstaendiger Service-Graph mit Ports (ollama, open-webui, qdrant, postgres, flowise, voice-processing, supervisor, auth, api, web, caddy)
- Compose-Profile und Layering-Regeln
- Healthcheck- und Monitoring-Prozeduren
- Backup-Strategie und Wiederherstellung
- Sicherheitsrichtlinien fuer Infrastruktur-Aenderungen
