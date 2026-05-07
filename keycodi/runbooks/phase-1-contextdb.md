# Runbook — Phase 1: Shared Context Window (Redis ContextDB)

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/CONTEXT-WINDOW.md`
**Milestones:** `keycodi/MILESTONES.md` § Phase 1

---

## Vorbedingungen

- Phase 0 ist `🟢 done` in `MILESTONES.md`.
- Sven hat die Architektur abgenickt (Label `keycodi:approved`).
- Es existieren noch keine `kidi/`-Pfade im Repo.

## Schritte (sequentiell)

### 1. Skelett anlegen

```bash
mkdir -p kidi/context_db tests/unit/kidi/context_db
touch kidi/context_db/{__init__.py,client.py,keys.py,zone_guard.py,errors.py}
touch tests/unit/kidi/context_db/__init__.py
```

Issue: `[phase-1] ContextDB: Paket-Skelett anlegen`.

### 2. `keys.py` — Key-Schema-Helfer

API: `make_key(zone, agent) -> str`, `parse_key(key) -> (zone, agent, uuid)`.
Test zuerst: `tests/unit/kidi/context_db/test_keys.py` — gültige + ungültige Inputs.

### 3. `zone_guard.py` — Zonen-Enforcement

API: `check_read(requester_max_zone, entry_zone)`, `check_write(zone, payload, env)`.
Refusal-Tests: `test_zone_enforcement.py`.

### 4. `errors.py`

Definiere: `ContextDBError`, `ZoneViolation`, `EgressViolation`, `KeyValueMismatch`, `SacredApprovalMissing`.

### 5. `client.py` — Redis-Client

- Verwendet `redis-py` (Dependency in `requirements.txt` ergänzen, nur falls noch nicht vorhanden).
- API exakt wie in `docs/agent/CONTEXT-WINDOW.md` §5.
- Egress-Guard: `os.environ.get("KIROBI_EGRESS_ALLOWED", "false") == "true"` blockiert FAMILY_PRIVATE/SACRED-Writes.
- TTL-Default: 86400 s.
- AOF-Persistenz wird auf Server-Seite konfiguriert (siehe Schritt 7).

### 6. Test-Suite

- `test_keys.py`
- `test_zone_enforcement.py` (mind. 1 Reject pro Zone-Kombination)
- `test_merge.py`
- `test_egress_guard.py`

Alle Tests müssen ohne laufendes Redis durchlaufen (FakeRedis oder Connection-Mock).

### 7. Compose-Integration

- `docker-compose.yml`: Redis-Service hinter Profile `kidi`, gebunden an `${KIROBI_BIND_HOST:-127.0.0.1}:6379`.
- AOF aktiv (`appendonly yes`, `appendfsync everysec`).
- Volume: `redis_data:/data`.
- Healthcheck: `redis-cli ping`.

### 8. Env-Beispiele

- `.env.example`:
  - `KIROBI_REDIS_PASSWORD=` (Default leer, Bootstrap generiert)
  - `KIROBI_EGRESS_ALLOWED=false`

### 9. Makefile

- `test-kidi:` Target, das nur die kidi-Test-Suite ausführt.
- `kidi-up:` Target: `docker compose --profile kidi up -d redis`.
- `kidi-down:` Target: `docker compose --profile kidi down`.

### 10. CI

- CI-Workflow (`.github/workflows/ci.yml`) so erweitern, dass `make test-kidi` ausgeführt wird.

## Definition of Done

Alle Items in `MILESTONES.md` Phase 1 abgehakt, CI grün, mind. ein Eintrag in `keycodi/learnings/`.

## Mögliche Stolpersteine

- `redis-py` als neue Dependency: vorher `gh-advisory-database` prüfen.
- Tests dürfen kein lebendes Redis erwarten.
- Egress-Guard nicht mit `KIROBI_BIND_HOST` verwechseln.

## Übergang

Nach `🟢 done`: `runbooks/phase-2-agent-skeletons.md`.
