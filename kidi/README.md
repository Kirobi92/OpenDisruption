---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kidi

MCP-kompatibler (Model Context Protocol) Server fuer den KeyCodi-Kontext-Layer. Stellt Agenten und Tools eine persistente, zonen-gesicherte Kontext-Datenbank sowie Backlog- und Zonen-Klassifizierungs-Tools ueber JSON-RPC 2.0 (stdio) bereit.

## Zweck

kidi ist die Laufzeit-Bruecke zwischen opencode/KeyCodi-Sitzungen und dem lokalen Kirobi-Oekosystem. Es ermoeglicht Agenten, Kontext-Informationen sitzungsuebergreifend zu speichern und abzurufen, ohne sensible Zonen zu verletzen.

## Starten

```bash
python -m kidi
```

Der Server kommuniziert ueber `stdin`/`stdout` mit newline-delimited JSON (MCP-Protokoll v2024-11-05).

## Unterstuetzte MCP-Tools

| Tool | Beschreibung |
|------|-------------|
| `context_store` | Speichert Key-Value-Paar (nur PUBLIC/WORKSPACE) |
| `context_get` | Liest einen Kontext-Eintrag |
| `context_list` | Listet alle gespeicherten Keys |
| `context_delete` | Loescht einen Eintrag |
| `backlog_query` | Fragt den kirobi_core-Backlog ab |
| `zone_classify` | Klassifiziert einen Pfad nach Sicherheitszone |

## Wichtige Dateien

| Datei/Ordner | Beschreibung |
|--------------|-------------|
| `serve.py` | MCP-Server-Implementierung; JSON-RPC-Dispatcher |
| `context_db/` | SQLite-Kontext-Store mit Zonen-Guard (siehe `context_db/README.md`) |
| `__main__.py` | Einstiegspunkt fuer `python -m kidi` |

## Abhaengigkeiten

- `kirobi_core.zones` — Zonen-Klassifizierung
- SQLite (Standardbibliothek) — Persistenz unter `~/.kirobi/context.db`
