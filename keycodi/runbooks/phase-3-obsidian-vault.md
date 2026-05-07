# Runbook — Phase 3: Obsidian-Vault + Knowledge-Graph

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/MULTI-AGENT-ARCHITECTURE.md` §3, `metadata/COLLECTION-MAPPING.md`
**Milestones:** `keycodi/MILESTONES.md` § Phase 3

---

## Vorbedingungen

- Phase 2 ist `🟢 done`. Alle vier Agenten antworten headless.
- `obsidian/`-Vault-Topologie aus Phase 0 existiert (READMEs, MOCs, Index).

## Schritte

### 1. Vault-Pfad-Konvention

Default: `${KIROBI_VAULT_PATH:-./obsidian}`. Im Repo liegt unter `obsidian/` ein Skelett (Phase 0); Production-Empfehlung: `~/kidi-vault/`.

ADR in `keycodi/decisions/`: Default-Pfad und Sync-Strategie.

### 2. `agents/obsidian/agent.py` erweitern

CRUD-Methoden:

- `create_note(zone, path, content, frontmatter)`
- `read_note(zone, path)`
- `update_note(zone, path, mutator)`
- `link_note(zone, src, target)` (legt `[[wikilink]]` an)
- `list_vault(zone, root="")`

Jede Methode prüft Zonen, schreibt nur in den zonen-passenden Vault-Unterordner (siehe `obsidian/README.md` Zone-Mapping).

### 3. Embedding-Bridge zu Qdrant

- Lookup: `(zone) → collection_name` aus `metadata/COLLECTION-MAPPING.md`.
- Refusal bei Mismatch (Zone → Collection-Zone weicht ab).
- Embeddings über das in `metadata/MODEL-REGISTRY.md` zu der Collection registrierte lokale Modell.
- **Niemals** Cloud-Embedding — auch nicht für PUBLIC, solange Sven nicht explizit erlaubt.

### 4. Daily-Note-Generator

`infra/scripts/obsidian-daily-note.sh`:

- Erzeugt `obsidian/shared-opendisruption/00-Index/daily/YYYY-MM-DD.md`.
- Inhalt: Phase-Status (aus `MILESTONES.md`), heute geschlossene Issues, Top-3-Learnings.
- Frontmatter: `zone: WORKSPACE`.
- Wird **nicht** als Cron installiert. Nur via `make obsidian-daily`.

### 5. MOC-Generator

`infra/scripts/obsidian-moc-generator.sh`:

- Pro Agent-Vault: aktualisiert `obsidian/agents/<name>/00-Index.md` mit allen Notes des Vaults.
- Shared-Vault: aktualisiert `obsidian/shared-opendisruption/00-Index/MOC.md`.

### 6. Tests

- `test_vault_crud.py`
- `test_zone_refusal_vault.py` (Schreiben in falsche Vault-Zone)
- `test_qdrant_collection_mapping.py` (Mismatch-Reject)
- `test_daily_note_render.py`
- `test_moc_generator.py`

### 7. Makefile

```
obsidian-daily:
obsidian-moc:
test-obsidian:
```

## Definition of Done

`make obsidian-daily` und `make obsidian-moc` laufen erfolgreich. Alle MOC-Dateien sind aktualisiert. Embedding-Mismatch wird abgelehnt.

## Mögliche Stolpersteine

- Vault-Pfad in Tests vs. Production verwechseln.
- Qdrant-Collection automatisch anlegen (verboten — nur Lookup).
- Daily-Note doppelt schreiben (Idempotenz prüfen).

## Übergang

Nach `🟢 done`: `runbooks/phase-4-kidi-keybrodi.md`.
