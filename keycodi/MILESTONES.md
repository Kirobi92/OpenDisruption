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
- [x] Telegram-Option entschieden: **A — Restricted Bridge**
- [x] Token-Storage entschieden: **lokale `.env`**
- [x] `install.sh`-Distribution entschieden: **repo-lokal, `--dry-run` Default**
- [x] Tailscale/LAN Web UI Entscheidung dokumentiert: **Caddy-only edge, Backends auf `127.0.0.1`**

## Phase 1 — Redis ContextDB

- [x] `kidi/context_db/client.py`
- [x] `kidi/context_db/keys.py`
- [x] `kidi/context_db/zone_guard.py`
- [x] `kidi/context_db/errors.py`
- [x] `docker-compose.yml` redis-Service hinter Profile `kidi`
- [x] `.env.example` Redis-Variablen
- [x] `tests/unit/kidi/context_db/test_keys.py`
- [x] `tests/unit/kidi/context_db/test_zone_enforcement.py`
- [x] `tests/unit/kidi/context_db/test_merge.py`
- [x] `tests/unit/kidi/context_db/test_egress_guard.py`
- [x] `Makefile` Target `make test-kidi`
- [ ] CI grün (nach PR-Merge)
- [x] Eintrag in `keycodi/learnings/`

## Phase 2 — Agenten-Skelette

- [x] `agents/_base/agent.py`
- [x] `agents/opencode/agent.py` + Dockerfile
- [x] `agents/openclaw/agent.py` + Dockerfile
- [x] `agents/hermes/agent.py` + Dockerfile
- [x] `agents/obsidian/agent.py` + Dockerfile
- [x] `docker-compose.yml` Profile `agents`
- [x] `Makefile` Targets `make agent-<name> TASK='...'`
- [x] Tests pro Agent (`smoke`, `zone_refusal`) — 52 Tests, 0.16s
- [ ] CI grün (nach PR-Merge)

## Phase 3 — Obsidian-Vault + Knowledge-Graph

- [x] `agents/obsidian/agent.py` Vault-CRUD
- [x] `infra/scripts/obsidian-daily-note.sh`
- [x] `infra/scripts/obsidian-moc-generator.sh`
- [x] `Makefile` Targets `make obsidian-daily`, `make obsidian-moc`
- [x] Embedding-Mismatch-Reject getestet (zone_collection_map Tests)
- [x] Pro-Agent-MOC generiert in `obsidian/agents/<name>/00-Index.md`
- [ ] CI grün

## Phase 4 — KIDI + KEYBRODI

- [ ] `kidi/core/collective_intelligence.py`
- [ ] `kidi/keybrodi/orchestrator.py`
- [ ] `kidi/keybrodi/routing_table.py` (statisch, aus `AGENT-DECISION-MATRIX.md`)
- [ ] Metrik-Schreiber → `kirobi-core/core-events.log`
- [ ] Tests: `test_synthesis.py`, `test_routing.py`, `test_zone_preservation.py`, `test_metrics.py`
- [ ] CI grün
- [ ] Handoff-Bereitschafts-Check (`HANDOFF-TO-KEYBRODI.md`)

## Phase 4.5 — External Agent Track (Sven-Override 2026-05-09)

ADR: `keycodi/decisions/0004-external-agent-integration.md`. Doku: `docs/agent/EXTERNAL-AGENT-INTEGRATION.md`.

- [x] ADR `0004-external-agent-integration.md`
- [x] Submodules `external/hermes-agent`, `external/openclaw`
- [x] `services/hermes-runtime/` (Wrapper-Dockerfile + `config/cli-config.yaml`)
- [x] `services/openclaw-gateway/` (README; Build via Submodule)
- [x] Compose-Profile `external-agents` mit beiden Services + Volumes
- [x] Caddy-Routes `/hermes/*`, `/openclaw/*` (HTTP + HTTPS) hinter `@not_edge_private`
- [x] Flowise-Healthcheck in `docker-compose.yml`
- [x] `infra/scripts/install-aionui.sh` mit `--dry-run` Default
- [x] `infra/scripts/healthcheck.sh` um Qdrant `/healthz`, Hermes, OpenClaw erweitert
- [x] `.env.example` Sektion "EXTERNAL AGENT TRACK"
- [x] Makefile-Targets `external-up`, `external-down`, `external-logs`, `aionui-install`, `external-update-submodules`
- [x] AGENTREGISTRY-Einträge 21–23
- [x] ZONE-POLICY-MATRIX um drei Zeilen erweitert
- [x] `docs/agent/EXTERNAL-AGENT-INTEGRATION.md`
- [ ] Submodule-Pin auf konkretes Tag (vor Merge)
- [ ] Live-Smoke-Test `make external-up` + Healthchecks grün
- [ ] `make integration-test` grün

## Phase 5 — Telegram (gated)

> Sperre: Option A ist bestätigt; Phase 5 startet trotzdem erst nach grünem Abschluss von Phase 4 und vorhandener lokaler `.env`-Konfiguration.

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
Phase 0: 🟡 IN PROGRESS  — 15/16 Items, Sven-Sign-off ausstehend
Phase 1: 🟢 DONE
Phase 2: 🟢 DONE
Phase 3: 🟢 DONE  — 6/7 Items, CI ausstehend
Phase 4: ⚪ PENDING
Phase 4.5: 🟡 IN PROGRESS — Code/Docs done, Live-Smoke + Pin offen
Phase 5: ⚪ PENDING (Option A gewählt, gated)
Phase 6: ⚪ PENDING
```
