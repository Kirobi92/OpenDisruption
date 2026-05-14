---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: LIVING DOCUMENT
---

# TECH_DEBT_REGISTER.md

Lebende Liste aller technischen Schulden mit Priorität, Aufwand, Risiko bei Änderung.

| ID | Kategorie | Befund | Pfad | Impact | Effort | Risiko | Priorität |
|---|---|---|---|---|---|---|---|
| TD-001 | Security | 5 Services binden auf `0.0.0.0` | `services/{api,auth,model-routing,media-processing,video-generation}/main.py` | hoch | niedrig | niedrig | **P0** |
| TD-002 | Security | JWT-Secret-Fallback `"CHANGEME-..."` | `services/auth/main.py:31` | hoch | niedrig | niedrig | **P0** |
| TD-003 | Security | CORS `["*"]` ohne Auth (model-routing) | `services/model-routing/main.py:109` | hoch | niedrig | niedrig | **P0** |
| TD-004 | Security | CORS `["*"]` + ohne Auth (personal-agents, nutzi) | `services/personal-agents/app/main.py`, `services/nutzi/` | hoch | niedrig | mittel | **P0** |
| TD-005 | Ops | Telegram-Service-Container nicht aktiv (obwohl `.env` konfiguriert) | `docker-compose.yml` | hoch | niedrig | niedrig | **P0** |
| TD-006 | Ops | Healthchecks fehlen: api, auth (TCP-only), orchestrator, voice-processing, telegram, hermes-runtime | `docker-compose.yml` | hoch | niedrig | niedrig | **P0** |
| TD-007 | Tests | 14/16 Backend-Services ohne Unit-Tests | `tests/unit/` | hoch | hoch | niedrig | **P1** |
| TD-008 | Architektur | `services/api/main.py` Monolith 2 262 LOC | `services/api/main.py` | hoch | mittel | mittel | **P1** |
| TD-009 | Architektur | `services/openclaw-gateway/` leer, aber im Compose | `services/openclaw-gateway/`, `docker-compose.yml` | niedrig | niedrig | niedrig | **P2** |
| TD-010 | Doku | 25 Root-MDs, viele redundant (ARCHITECTURE vs PROJECT-ARCHITECTURE, etc.) | Root | mittel | niedrig | niedrig | **P1** |
| TD-011 | Architektur | Hermes-Memory single-file statt per-User | `services/hermes-runtime/config/cli-config.yaml` | hoch | niedrig | niedrig | **P0** |
| TD-012 | Frontend | 6 aktive Web-Apps (3.2 GB node_modules) | `apps/{web,portal,admin,dashboard,voice,web-svelte}` | mittel | hoch | mittel | **P2** |
| TD-013 | Code-Quality | Bare `except Exception:` in Ingest | `services/ingest/main.py:465,522,599,601,621` | mittel | niedrig | niedrig | **P1** |
| TD-014 | Code-Quality | 30 `print()` statt Logger | mehrere Services | niedrig | niedrig | niedrig | **P2** |
| TD-015 | Config | 183 Env-Vars ohne Schema-Validierung | `docker-compose.yml`, `.env.example` | mittel | mittel | niedrig | **P1** |
| TD-016 | Config | Hardcoded `"changeme"` Postgres-Pass-Fallback | `services/{api,auth,telegram}/main.py` | hoch | niedrig | niedrig | **P0** |
| TD-017 | Architektur | Postgres-Schema-Bootstrap in 4 Services dupliziert | `services/{api,auth,ingest,telegram}/main.py` | mittel | mittel | mittel | **P2** |
| TD-018 | Architektur | Service-URLs hardcoded statt Service-Discovery / shared `urls.py` | mehrere Services | niedrig | mittel | niedrig | **P2** |
| TD-019 | Performance | Sync-Calls in async-Routen | mehrere | mittel | mittel | mittel | **P2** |
| TD-020 | Ops | Keine Memory/CPU-Limits in Compose (außer GPU) | `docker-compose.yml` | mittel | niedrig | niedrig | **P1** |
| TD-021 | Ops | RW-Mounts wo RO reicht (`./kirobi-core:/kirobi-core`) | `docker-compose.yml` (supervisor) | niedrig | niedrig | niedrig | **P2** |
| TD-022 | Naming | `kirobi-core/` (MD) vs. `kirobi_core/` (Python) | Repo-Wurzel | niedrig | hoch | hoch | **P3** |
| TD-023 | Architektur | 4 Orchestrierungs-Schichten ohne klare Abgrenzung (orchestrator, supervisor, KeyCodi, Hermes) | mehrere | mittel | niedrig (nur Doku) | niedrig | **P1** |
| TD-024 | CI | Kein Coverage-Report (`pytest --cov`) | `Makefile`, `.github/workflows/` | mittel | niedrig | niedrig | **P1** |
| TD-025 | CI | Keine Container-Image-Builds in CI | `.github/workflows/` | mittel | mittel | niedrig | **P2** |
| TD-026 | Backup | `infra/scripts/backup.sh` nie validiert (Restore-Test fehlt) | `infra/scripts/backup.sh` | hoch | niedrig | niedrig | **P0** |
| TD-027 | Doku | Datenfluss `sources/ → extracts/ → canon/` nicht dokumentiert | `docs/` | mittel | niedrig | niedrig | **P1** |
| TD-028 | Code-Quality | Type-Hints lückenhaft (insb. ältere Services) | mehrere | niedrig | hoch | niedrig | **P3** |
| TD-029 | Apps | `apps/desktop`, `apps/mobile` Scaffolds noch im Compose-Routing-Bereich | `apps/`, `docker-compose.yml` | niedrig | niedrig | niedrig | **P2** |
| TD-030 | Dependencies | Pinning inkonsistent (`>=` vs `==`) | `services/*/requirements.txt`, `apps/*/package.json` | mittel | mittel | niedrig | **P2** |
| TD-031 | Hermes | MCP `filesystem` deckt `/Datenspeicher/` nicht ab | `services/hermes-runtime/config/cli-config.yaml` | mittel | niedrig | niedrig | **P0** |
| TD-032 | Hermes | Kein Telegram-User-ID-Routing zu personal-agents | `agents/hermes/`, `services/hermes-runtime/` | hoch | mittel | niedrig | **P1** |

**Gesamt: 32 Schulden**
- P0 (sofort): **9**
- P1 (Sprint 1): **9**
- P2 (Sprint 2–3): **11**
- P3 (Backlog): **3**

## Pflege-Regel
- Jede gelöste Schuld → Zeile mit `~~Strikethrough~~` + Datum + Commit-Hash
- Neue Schulden hinzufügen mit nächster freier ID
- Quartalsweise Re-Priorisierung
