---
zone: WORKSPACE
agent: keycodi
created: 2026-05-07
updated: 2026-05-07
tags: [learnings, phase3, obsidian, vault-crud, knowledge-graph]
phase: 3
---

# 0003 — Phase 3: Obsidian-Vault + Knowledge-Graph

## Was wurde implementiert

### `agents/obsidian/agent.py` — echtes Vault-CRUD (Phase 3)
- **vault_read**: Note lesen, Backlinks extrahieren (`[[Wikilinks]]`)
- **vault_write**: Note anlegen/überschreiben, optionaler Frontmatter-Präfix
- **vault_delete**: Note löschen (nur Files, kein Verzeichnis-Delete)
- **vault_list**: Alle Markdown-Dateien in einem Verzeichnis auflisten
- **vault_query_links**: Outgoing + Incoming Links einer Note
- **daily_note**: Daily-Note idempotent anlegen (`shared-opendisruption/99-Inbox/YYYY-MM-DD-daily.md`)
- **moc**: Map-of-Content (00-Index.md) für einen Agenten generieren/aktualisieren
- **zone_collection_map**: Mapping Zone → Qdrant-Collection + Embedding-Modell + Dimensionen

### Infra-Skripte
- `infra/scripts/obsidian-daily-note.sh` — Idempotente Daily-Note, `--dry-run`-Support
- `infra/scripts/obsidian-moc-generator.sh` — MOC-Generator für alle oder einen Agenten

### Makefile
- `make obsidian-daily` — Daily-Note anlegen
- `make obsidian-moc` — alle MOCs; `make obsidian-moc AGENT=opencode` — einen Agenten

### Tests
- 39 neue Unit-Tests (vault_read, vault_write, vault_delete, vault_list, vault_query_links, daily_note, moc, zone_collection_map, sacred-reject, FAMILY_PRIVATE-approval)
- Gesamtsuite: 246 Tests, 2.66s, 0 Fehler

## Wichtige Entscheidungen

### Embedding-Mismatch-Reject via `zone_collection_map`
Statt Qdrant direkt zu integrieren (kein Qdrant-Container im Unit-Test verfügbar), wird das Mapping
`Zone → Collection → Modell → Dimensionen` als statische Quelle der Wahrheit im Agent selbst gepflegt
und via `zone_collection_map`-Task ausgeliefert. Der hermes-extractor liest dieses Mapping bevor
er Embeddings an Qdrant schickt und kann so Dimension-Mismatches früh ablehnen.

- PUBLIC: `nomic-embed-text`, 768d → `kirobi_public`
- WORKSPACE: `bge-m3`, 1024d → `kirobi_workspace`
- FAMILY_PRIVATE: `bge-m3`, 1024d → `kirobi_family`

### Sacred-Pfad-Guard ist Pfad-basiert, nicht Zone-basiert
Ein `sacred/`-Pfad wird unabhängig von Zone, Approval-Token und Task-Typ abgelehnt.
Das ist defensive Programmierung: Selbst wenn ein Angreifer Zone und Token fälscht, bleibt der Pfad-Check aktiv.

### Vault-Write für FAMILY_PRIVATE erfordert Approval-Token
Read ist ohne Token erlaubt (lokal-only, kein Egress). Write erfordert `approval_token` — konsistent
mit der Grundregel aus `AGENT-DECISION-MATRIX.md §B.2`.

### `tmp_path`-Fixture für alle Vault-Tests
Alle File-I/O läuft in pytest-`tmp_path` — kein Zugriff auf den echten Vault, kein Testdaten-Rückstand.

## Gotchas

- Makefile-`$(if VAR,...)` expandiert auf `1` wenn AGENT nicht gesetzt ist wegen GNU Make `--dry-run` target-order. Workaround: Inline-Shell-`if`-Test.
- `vault_read` ohne `path` im Payload → `success=False` (nicht Exception). Ältere Skelett-Tests
  haben das nicht abgedeckt — der `test_zone_refusal.py`-Test musste angepasst werden.
- `obsidian-moc-generator.sh` nutzt `mapfile` → Bash 4+ erforderlich (nicht dash-kompatibel, `set -Eeuo pipefail` ist korrekt).
