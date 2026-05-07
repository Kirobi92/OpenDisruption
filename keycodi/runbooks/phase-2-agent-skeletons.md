# Runbook — Phase 2: Agenten-Skelette

**Zone:** WORKSPACE
**Spezifikation:** `docs/agent/MULTI-AGENT-ARCHITECTURE.md` §3
**Milestones:** `keycodi/MILESTONES.md` § Phase 2

---

## Vorbedingungen

- Phase 1 ist `🟢 done`. ContextDB-Tests sind grün.

## Schritte

### 1. Verzeichnisse

```bash
mkdir -p agents/_base agents/{opencode,openclaw,hermes,obsidian}
mkdir -p tests/unit/agents/{opencode,openclaw,hermes,obsidian}
```

### 2. Basisklasse `agents/_base/agent.py`

- Abstrakte Klasse `BaseAgent`.
- Felder: `name`, `allowed_read_zones`, `allowed_write_zones`.
- Methoden:
  - `__init__(context_db: ContextDB)` (Phase-1-Client).
  - `handle(task: dict) -> dict` (abstract).
  - `read_context(zone, **filters)` mit Zonen-Check.
  - `write_context(zone, payload, confidence=0.0)` mit Zonen-Check.
  - `audit(event_type, **kwargs)` schreibt nach `kirobi-core/core-events.log`.
- Refusal: jede Zonen-Verletzung wirft `ZoneViolation` aus `kidi.context_db.errors`.

### 3. Agent-Implementierungen

Pro Agent: `agents/<name>/agent.py`, das `BaseAgent` erbt, einen Echo-Handler implementiert (`handle(task) -> {"echo": task}`) und seine Zonen aus `metadata/AGENTREGISTRY.md` deklariert.

| Agent     | allowed_read_zones                          | allowed_write_zones                         |
|-----------|---------------------------------------------|---------------------------------------------|
| opencode  | PUBLIC, WORKSPACE                           | PUBLIC, WORKSPACE                           |
| openclaw  | PUBLIC, WORKSPACE, QUARANTINE               | PUBLIC, WORKSPACE, QUARANTINE               |
| hermes    | PUBLIC, WORKSPACE                           | PUBLIC, WORKSPACE                           |
| obsidian  | PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal)   | PUBLIC, WORKSPACE, FAMILY_PRIVATE (lokal)   |

### 4. CLI-Treiber

Makefile-Target pro Agent:

```
agent-opencode:
	python -m agents.opencode.agent --task "$(TASK)"
```

Identisch für `openclaw`, `hermes`, `obsidian`.

### 5. Dockerfile pro Agent

Schmal, basierend auf `python:3.11-slim`. Compose-Eintrag hinter Profile `agents`.

### 6. Tests pro Agent

- `test_smoke.py` — Echo-Verhalten.
- `test_zone_refusal.py` — Schreibe in untersagte Zone → `ZoneViolation`.
- `test_context_roundtrip.py` — `write_context` + `read_context` mit identischem Inhalt.

### 7. CI

`.github/workflows/ci.yml`: `make test-agents` ergänzen.

## Definition of Done

Alle vier Agenten antworten headless auf `make agent-<name> TASK='ping'`. Refusal-Tests grün. Compose `--profile agents` startet.

## Mögliche Stolpersteine

- Vergessen, `obsidian`-Agent auf einen Host mit `KIROBI_EGRESS_ALLOWED=false` zu beschränken (Compose-Annotation).
- ContextDB-Verbindung im Container: Service-Name `redis` statt `127.0.0.1`.

## Übergang

Nach `🟢 done`: `runbooks/phase-3-obsidian-vault.md`.
