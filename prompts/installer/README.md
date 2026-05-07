---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/installer – Installer-Agent-Prompts

System-Prompts und Gesprächsleitfäden für den `installer-agent`, der neue Nutzer freundlich und schrittweise durch die Kirobi-Installation führt.

## Zweck

Der Installer-Agent ist der erste Kontaktpunkt für neue Nutzer. Seine Prompts müssen technisch präzise, aber verständlich sein – und Vertrauen aufbauen, indem sie das Local-First-Prinzip erklären und bei Fehlern ruhig und lösungsorientiert reagieren.

## Enthaltene Prompts

| Datei | Beschreibung |
|-------|-------------|
| `setup-wizard-prompt.md` | Haupt-System-Prompt für den Setup-Wizard |

## Namenskonvention

```
[aufgabe]-[version].md
Beispiele:
  setup-wizard-v1.md
  prerequisites-check-v1.md
  env-configuration-v1.md
  first-steps-v1.md
```

## Installer-Ablauf

Der Setup-Wizard führt durch folgende Phasen:

1. **Begrüßung** – Kirobi vorstellen, Local-First erklären
2. **Voraussetzungen prüfen** – Docker, GPU, Speicher, Betriebssystem
3. **`.env`-Konfiguration** – Schritt für Schritt durch kritische Variablen
4. **Services starten** – `make up`, Gesundheitsprüfung
5. **Modelle laden** – Empfohlene Ollama-Modelle herunterladen
6. **Erste Schritte** – Kurzeinführung in die wichtigsten Funktionen

## Sicherheitsregeln für Installer-Prompts

- Keine System-Modifikationen außerhalb von `~/kirobi/`
- Keine Secrets in Prompt-Ausgaben
- Bei kritischen Aktionen immer Bestätigung einholen
- Fehler erklären, nicht verschweigen

## Verwandte Dateien

- `install.sh` – Idempotentes Installations-Skript
- `infra/scripts/validate-env.sh` – Env-Validierung
- `DEVELOPER-RUNBOOK.md` – CLI-Workflows für Entwickler
