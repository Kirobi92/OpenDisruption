---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kirobi_core

Importierbares Python-Paket und CLI-Stdlib fuer das OpenDisruption-Oekosystem. Stellt Kern-Funktionen bereit: Zonen-Klassifizierung, Backlog-Verwaltung, Agent-Registry, Gesundheitspruefungen, autonome Ausfuehrung und KeyCodi-Missionsplanung.

## Zweck

`kirobi_core` ist die gemeinsame Grundlage aller Python-Services und Agenten. Es enthaelt keine externen Abhaengigkeiten jenseits der Standardbibliothek und kann direkt als CLI verwendet werden:

```bash
python -m kirobi_core doctor
python -m kirobi_core scan
python -m kirobi_core backlog --limit 5
python -m kirobi_core keycodi "Missionsbeschreibung"
python -m kirobi_core status --json
python -m kirobi_core registry
python -m kirobi_core autonomous-once
```

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `cli.py` | Einstiegspunkt fuer alle CLI-Subkommandos |
| `zones.py` | Fuenf-Zonen-Sicherheitsmodell: Klassifizierung von Pfaden nach PUBLIC, WORKSPACE, FAMILY_PRIVATE, QUARANTINE, SACRED |
| `config.py` | Konfigurationsspeicher; liest `.env` und Umgebungsvariablen |
| `scanner.py` | Repository-Scan: erstellt JSON-Zusammenfassung der Struktur |
| `backlog.py` | Backlog-Generierung und Priorisierung offener Aufgaben |
| `registry.py` | Agent-Registry: listet und verwaltet registrierte Agenten |
| `doctor.py` | Umgebungs-Gesundheitspruefungen (offline und live) |
| `keycodi.py` | Missionsplanung fuer den KeyCodi-Orchestrator |
| `orchestrator.py` | Aufgaben-Orchestrierung zwischen Agenten |
| `autonomous.py` | Autonomer Ausfuehrungs-Loop (`run_once`, `run_loop`) |
| `audit.py` | Audit-Logger fuer `kirobi-core/core-events.log` |
| `bridge.py` | Bruecke zu externen Services (Ollama, API) |
| `interview.py` | Gefuehrtes Interview zur Profil-Erstellung |
| `notify.py` | Benachrichtigungs-Hilfsfunktionen |
| `services.py` | Service-Status-Abfragen |
| `__main__.py` | Erlaubt `python -m kirobi_core` |

## Sicherheit

Alle Operationen respektieren das Fuenf-Zonen-Modell. Destruktive Aktionen ausserhalb von WORKSPACE/PUBLIC werden abgelehnt. Unbekannte Pfade werden konservativ als SACRED klassifiziert.
