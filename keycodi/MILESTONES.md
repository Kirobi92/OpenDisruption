# KeyCodi — Milestones (Tracking-Liste)

**Zone:** WORKSPACE
**Pflege:** KeyCodi nach jedem grünen Test-Lauf.
**Regel:** Erst abhaken, wenn Test grün **und** in Commit referenziert.

Legende: `[ ]` offen · `[x]` erledigt · `[!]` blockiert (Verweis auf Issue)

---

## Phase 0 — Architektur-Sign-off

- [x] `docs/agent/MULTI-AGENT-ARCHITECTURE.md`
- [x] `docs/agent/KIDI-ENGINE.md`
- [x] `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`
- [x] `docs/agent/CONTEXT-WINDOW.md`
- [x] `docs/agent/TELEGRAM-INTEGRATION.md`
- [x] `AGENT-DECISION-MATRIX.md`
- [x] `metadata/ZONE-POLICY-MATRIX.md` (6 neue Agenten)
- [x] `metadata/AGENTREGISTRY.md` (Sektionen 15–20)
- [x] `keycodi/` HQ angelegt
- [x] `obsidian/` Vault-Topologie angelegt
- [x] `.github/ISSUE_TEMPLATE/` Backlog-Templates
- [ ] Sven nickt Architektur ab
- [ ] Telegram-Option (A/B/C) entschieden
- [ ] Token-Storage entschieden (falls A)
- [ ] `install.sh`-Distribution entschieden

## Phase 1 — Redis ContextDB

- [ ] `kidi/context_db/client.py`
- [ ] `kidi/context_db/keys.py`
- [ ] `kidi/context_db/zone_guard.py`
- [ ] `kidi/context_db/errors.py`
- [ ] `docker-compose.yml` redis-Service hinter Profile `kidi`
- [ ] `.env.example` Redis-Variablen
- [ ] `tests/unit/kidi/context_db/test_keys.py`
- [ ] `tests/unit/kidi/context_db/test_zone_enforcement.py`
- [ ] `tests/unit/kidi/context_db/test_merge.py`
- [ ] `tests/unit/kidi/context_db/test_egress_guard.py`
- [ ] `Makefile` Target `make test-kidi`
- [ ] CI grün
- [ ] Eintrag in `keycodi/learnings/`

## Phase 2 — Agenten-Skelette

- [ ] `agents/_base/agent.py`
- [ ] `agents/opencode/agent.py` + Dockerfile
- [ ] `agents/openclaw/agent.py` + Dockerfile
- [ ] `agents/hermes/agent.py` + Dockerfile
- [ ] `agents/obsidian/agent.py` + Dockerfile
- [ ] `docker-compose.yml` Profile `agents`
- [ ] `Makefile` Targets `make agent-<name> TASK='...'`
- [ ] Tests pro Agent (`smoke`, `zone_refusal`)
- [ ] CI grün

## Phase 3 — Obsidian-Vault + Knowledge-Graph

- [ ] `agents/obsidian/agent.py` Vault-CRUD
- [ ] `infra/scripts/obsidian-daily-note.sh`
- [ ] `infra/scripts/obsidian-moc-generator.sh`
- [ ] `Makefile` Targets `make obsidian-daily`, `make obsidian-moc`
- [ ] Embedding-Mismatch-Reject getestet
- [ ] Pro-Agent-MOC generiert in `obsidian/agents/<name>/00-Index.md`
- [ ] CI grün

## Phase 4 — KIDI + KEYBRODI

- [ ] `kidi/core/collective_intelligence.py`
- [ ] `kidi/keybrodi/orchestrator.py`
- [ ] `kidi/keybrodi/routing_table.py` (statisch, aus `AGENT-DECISION-MATRIX.md`)
- [ ] Metrik-Schreiber → `kirobi-core/core-events.log`
- [ ] Tests: `test_synthesis.py`, `test_routing.py`, `test_zone_preservation.py`, `test_metrics.py`
- [ ] CI grün
- [ ] Handoff-Bereitschafts-Check (`HANDOFF-TO-KEYBRODI.md`)

## Phase 5 — Telegram (gated)

> Sperre: nur starten, wenn Sven Option A bestätigt.

- [ ] `agents/_telegram/zone_filter.py`
- [ ] Sechs Bot-Handler unter Profile `telegram`
- [ ] Redis-ACL-User für Telegram
- [ ] `infra/scripts/daily-team-meeting.sh` (Opt-in)
- [ ] Reject-Pfad-Tests pro Zone
- [ ] `.env.example` Token-Placeholder, `KIROBI_TELEGRAM_ENABLED=false`
- [ ] CI grün

## Phase 6 — install.sh + Polish

- [ ] `install.sh` mit `--dry-run`-Default
- [ ] `README.md` aktualisiert
- [ ] `BENUTZERHANDBUCH.md` aktualisiert
- [ ] `QUICK-REFERENCE.md` aktualisiert
- [ ] `CHANGELOG.md` aktualisiert
- [ ] CI grün

---

## Status-Zeile

```
Phase 0: 🟡 IN PROGRESS  — 11/15 Items, Sven-Sign-off ausstehend
Phase 1: ⚪ PENDING
Phase 2: ⚪ PENDING
Phase 3: ⚪ PENDING
Phase 4: ⚪ PENDING
Phase 5: ⚪ PENDING (gated)
Phase 6: ⚪ PENDING
```
