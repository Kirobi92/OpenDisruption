---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/unit/agents/obsidian

Unit-Tests für den `ObsidianAgent` — den einzigen Agenten mit Schreibzugriff auf den Obsidian-Vault.

## Dateien

- `test_handle_smoke.py` — Vollständige CRUD-Tests: `vault_read`, `vault_write`, `vault_delete`, `vault_list`, `vault_query_links`, `daily_note`, `moc`, `zone_collection_map`
- `test_zone_refusal.py` — Zone-Enforcement: stellt sicher, dass SACRED und QUARANTINE immer abgelehnt werden

## Was getestet wird

### Smoke-Tests (`test_handle_smoke.py`)

Alle Tests arbeiten mit einem temporären Vault (`tmp_path`-Fixture) — kein Zugriff auf den echten Vault.

| Klasse | Prüft |
|--------|-------|
| `TestVaultRead` | Lesen existierender/fehlender Notes, Backlink-Extraktion, Fehler ohne Pfad |
| `TestVaultWrite` | Neue Note anlegen, Verzeichnisse erstellen, Frontmatter-Prepend, Update |
| `TestVaultDelete` | Löschen mit `approval_token`, Fehler bei fehlendem Pfad |
| `TestVaultList` | Vault-Listing, Unterverzeichnis-Filter, Fehler bei nicht-existentem Pfad |
| `TestVaultQueryLinks` | Ausgehende und eingehende Wiki-Links |
| `TestDailyNote` | Anlegen und Idempotenz (zweiter Aufruf setzt `created: False`) |
| `TestMoc` | Map-of-Content-Generierung (`00-Index.md`) pro Agent-Verzeichnis |
| `TestZoneCollectionMap` | Embedding-Modell und Dimension pro Zone (nomic-embed-text 768d / bge-m3 1024d) |
| `TestSacredPathRefusal` | `sacred/`-Pfade werden unabhängig von Zone und Token immer abgelehnt |
| `TestFamilyPrivateApproval` | Schreiben in FAMILY_PRIVATE erfordert `approval_token`; Lesen nicht |

### Zone-Refusal-Tests (`test_zone_refusal.py`)

Prüft, dass SACRED- und QUARANTINE-Zonen grundsätzlich abgelehnt werden, FAMILY_PRIVATE aber erlaubt ist (der Obsidian-Agent ist der einzige neue Agent mit diesem Recht).

## Ausführen

```bash
# Nur diese Test-Gruppe
python -m pytest tests/unit/agents/obsidian -v

# Mit Keyword-Filter
python -m pytest tests/unit -k obsidian -q
```

## Abhängigkeiten

- `agents.obsidian.agent.ObsidianAgent`
- `agents._base.agent.Task`
- `pytest` (kein Mock-Framework nötig — echter File-I/O in `tmp_path`)
