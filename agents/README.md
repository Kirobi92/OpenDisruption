---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# agents

Python-Agenten-Paket des OpenDisruption-Oekosystems. Enthaelt spezialisierte Agenten-Implementierungen sowie die gemeinsame Basisklasse, von der alle Agenten erben.

## Zweck

Jeder Agent kapselt eine spezifische Faehigkeit (z.B. Ingestion, Obsidian-Sync, opencode-Integration) und implementiert das `BaseAgent`-Interface aus `_base/`. Agenten kommunizieren ueber den kidi-Kontext-Layer und respektieren das Fuenf-Zonen-Sicherheitsmodell.

## Struktur

| Ordner/Datei | Beschreibung |
|--------------|-------------|
| `_base/` | Abstrakte Basisklasse `BaseAgent` mit Task-Handling, Zonen-Pruefung und optionaler ContextDB-Integration |
| `hermes/` | Hermes-Extractor-Agent: Ingestion und Klassifizierung von Rohdaten aus `sources/` |
| `obsidian/` | Obsidian-Sync-Agent: Synchronisierung mit dem Obsidian-Vault |
| `openclaw/` | OpenClaw-Agent (Zweck siehe `openclaw/`) |
| `opencode/` | opencode-Integrations-Agent: Bruecke zwischen opencode-Sitzungen und dem Kirobi-Backend |
| `requirements.txt` | Python-Abhaengigkeiten fuer alle Agenten |
| `__init__.py` | Paket-Initialisierung |

## Gemeinsame Konzepte

- Alle Agenten erben von `agents._base.agent.BaseAgent`
- Aufgaben werden als `Task`-Objekte mit `task_type`, `zone` und `payload` uebergeben
- Zonen-Verletzungen werden als Ausnahmen geworfen, bevor eine Aufgabe ausgefuehrt wird
- Agenten koennen optional den kidi-ContextDB-Client nutzen (graceful degradation wenn kidi nicht verfuegbar)

## Ausfuehren

Einzelne Agenten werden typischerweise als Docker-Container betrieben (je ein `Dockerfile` pro Agent) oder direkt ueber den `supervisor`-Service gesteuert.
