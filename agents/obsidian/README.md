---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Agent: obsidian

Vault-Agent für Lese- und Schreiboperationen auf dem Obsidian-Markdown-Vault. Verwaltet Notes, Daily Notes, Backlink-Graphen und Maps of Content (MOC). Kein Embedding — Qdrant-Collections werden ausschließlich von `hermes-extractor` befüllt.

## Dateien

- `agent.py` — Vollständige Implementierung von `ObsidianAgent` (Phase 3)
- `__init__.py` — Modul-Export
- `Dockerfile` — Container-Definition

## Unterstützte Task-Typen

| Task-Typ | Beschreibung |
|----------|--------------|
| `vault_read` | Note lesen |
| `vault_write` | Note schreiben oder anlegen |
| `vault_delete` | Note löschen (reversibel via git) |
| `vault_list` | Alle Notes in einem Verzeichnis auflisten |
| `vault_query_links` | Eingehende und ausgehende Backlinks ermitteln |
| `daily_note` | Daily-Note für heute anlegen (idempotent) |
| `moc` | Map-of-Content für einen Agenten generieren |
| `zone_collection_map` | Mapping Zone zu Qdrant-Collection ausgeben |

## Erlaubte Zonen

Input und Output: `PUBLIC`, `WORKSPACE`, `FAMILY_PRIVATE` (lokal-only, kein Cloud-Egress)

## Sicherheits-Invarianten

- `sacred/`-Pfade werden immer abgelehnt, unabhängig von Zone
- `vault_write` und `vault_delete` in `FAMILY_PRIVATE` erfordern ein `approval_token`
- Vault-Pfad konfigurierbar via `KIROBI_VAULT_PATH` (Standard: `obsidian/`)
