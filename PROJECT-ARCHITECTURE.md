# Project Architecture — OpenDisruption / Kirobi OS

> Audience: agents and engineers who need a complete mental model of the
> system in 10 minutes. For domain & philosophy see `PROJECT-CHARTER.md` and
> `ARCHITECTURE.md`; for governance see `CLAUDE.md` and `metadata/`.

---

## 1. North star

A **local-first**, **agent-driven**, **zone-aware** personal operating system
for one family and the businesses around it. Five non-negotiable properties:

1. Local-first — sensitive data never leaves the host.
2. Agent-friendly — every operation is scriptable, idempotent, observable.
3. Zone-secured — five zones (`PUBLIC` → `SACRED`) gate every byte.
4. Reproducible — `install.sh` rebuilds the system from a blank box.
5. Extensible — new agents/services plug in via Compose profiles + zone tags.

---

## 2. Logical layers

```
┌─────────────────────────────────────────────────────────────────┐
│ 7  Experience layer    family PWA · Open-WebUI · voice          │
├─────────────────────────────────────────────────────────────────┤
│ 6  Agent layer         kirobi-core · samira · sineo · hermes …  │
├─────────────────────────────────────────────────────────────────┤
│ 5  Service layer       services/{auth,api,retrieval,…}          │
├─────────────────────────────────────────────────────────────────┤
│ 4  Knowledge layer     canon/  experiences/  extracts/  clusters│
├─────────────────────────────────────────────────────────────────┤
│ 3  Storage layer       Postgres · Qdrant · file system zones    │
├─────────────────────────────────────────────────────────────────┤
│ 2  Model layer         Ollama (LLM) · Whisper (STT) · Piper     │
├─────────────────────────────────────────────────────────────────┤
│ 1  Infra layer         Docker Compose · Caddy · mDNS · backups  │
├─────────────────────────────────────────────────────────────────┤
│ 0  Host                Linux/macOS · CPU/GPU · disk · network   │
└─────────────────────────────────────────────────────────────────┘
```

Information flow:

```
sources/  →  hermes-extractor  →  extracts/  →  clustering  →
clusters/ →  canon-update      →  canon/    →  capture     →
experiences/                                 ↓
                                       (back into RAG)
```

---

## 3. Repository topology

| Path | Zone | Purpose |
|------|------|---------|
| `install.sh` | PUBLIC | one-command bootstrap |
| `Makefile` | PUBLIC | developer entry points |
| `docker-compose.yml` | WORKSPACE | service graph |
| `.env.example` | PUBLIC | env template (placeholders only) |
| `apps/` | WORKSPACE | front-ends (web/desktop/mobile/voice/installer) |
| `services/` | WORKSPACE | back-end micro-services (FastAPI etc.) |
| `kirobi-core/` & `kirobi_core/` | WORKSPACE | supervisor agent (Python) |
| `infra/` | WORKSPACE | scripts, Caddy, compose helpers, monitoring |
| `config/templates/` | WORKSPACE | reusable config templates (compose, env, caddy, nginx) |
| `metadata/` | WORKSPACE | governance: zones, security, registries |
| `prompts/` | WORKSPACE | agent prompt library |
| `models/` | WORKSPACE | manifests + cached weights (gitignored) |
| `templates/` | PUBLIC | document templates (briefs, reviews) |
| `docs/` & `docs/agent/` | PUBLIC | end-user & agent documentation |
| `tests/` | WORKSPACE | unit + integration tests |
| `canon/` | mixed | curated knowledge (PUBLIC subtree, FAMILY subtree) |
| `experiences/` | FAMILY_PRIVATE | learnings, projects, family memory |
| `extracts/` | mixed | extracted knowledge sorted by zone |
| `clusters/` | WORKSPACE | semantic clusters |
| `sources/inbox/` | QUARANTINE | raw, unverified inbound |
| `quarantine/` | QUARANTINE | suspicious / pending review |
| `sacred/` | SACRED | highest confidentiality |
| `archive/snapshots/` | WORKSPACE | backup output |
| `.kirobi/` | WORKSPACE | runtime facts (`install.json`, reports) |

---

## 4. Service graph (Compose)

| Service | Image | Port (host bind) | Depends on | Profile |
|---------|-------|------------------|------------|---------|
| `ollama` | `ollama/ollama` | `11434` | – | all |
| `open-webui` | `ghcr.io/open-webui/open-webui` | `3000` | ollama | all |
| `qdrant` | `qdrant/qdrant` | `6333/6334` | – | all |
| `postgres` | `postgres:16-alpine` | `5432` | – | all |
| `flowise` | `flowiseai/flowise` | `3001` | postgres | all |
| `auth` | `services/auth` | `8002` | postgres | all |
| `api` | `services/api` | `8003` | postgres, qdrant | all |
| `web` | `apps/web` | `3002` | auth, api | all |
| `caddy` | `caddy:2` | `80/443` | web, api | production |
| `voice-*` | `services/voice-processing` | – | ollama | voice-full |

Profiles supported by `install.sh` (templates in `config/templates/compose/`):

- `minimal`  — Ollama + Postgres + Qdrant only
- `cpu`      — full stack on CPU (small models)
- `nvidia`   — full stack with NVIDIA GPU
- `amd`      — full stack with ROCm
- `voice-full` — adds Whisper + Piper services
- `production`  — enables Caddy + monitoring + restart policies
- `development` — exposes ports on `0.0.0.0`, enables hot-reload mounts

All ports default-bind to `${KIROBI_BIND_HOST:-127.0.0.1}` — local-first.

---

## 5. Data layer

- **Postgres** holds: auth schema (users, sessions, audit_log), service
  metadata, structured agent state. Row-level zone tagging.
- **Qdrant** holds **seven** named collections (see
  `metadata/COLLECTION-MAPPING.md`):

  | Collection | Embed model | Dim | Zone |
  |------------|-------------|-----|------|
  | `kirobi_workspace`   | `bge-m3`            | 1024 | WORKSPACE |
  | `kirobi_family`      | `bge-m3`            | 1024 | FAMILY_PRIVATE |
  | `kirobi_canon`       | `bge-m3`            | 1024 | mixed |
  | `kirobi_experiences` | `bge-m3`            | 1024 | FAMILY_PRIVATE |
  | `kirobi_public`      | `nomic-embed-text`  | 768  | PUBLIC |
  | `kirobi_code`        | `nomic-embed-text`  | 768  | WORKSPACE |
  | `kirobi_quarantine`  | `nomic-embed-text`  | 768  | QUARANTINE |

- **File system** is the system of record. Postgres/Qdrant are derived
  indices; both can be rebuilt from files via `make scan` + reingest.

---

## 6. Agent layer

`kirobi-core` is the supervisor; specialised agents do the work:

| Agent | Read | Write | Special |
|-------|------|-------|---------|
| `kirobi-core` | all | all except SACRED | gate-keeper |
| `kirobi-architect` | PUBLIC, WORKSPACE | same | design only |
| `kirobi-coder` | PUBLIC, WORKSPACE | same | code only |
| `kirobi-ops` | PUBLIC, WORKSPACE, QUARANTINE | same | infra |
| `kirobi-observer` | all (read-mostly) | PUBLIC, WORKSPACE | reports |
| `hermes-extractor` | PUBLIC, WORKSPACE, QUARANTINE | same | ingestion |
| `samira-heart` | + FAMILY_PRIVATE | PUBLIC, FAMILY_PRIVATE | family mediation |
| `sineo-creator` | + FAMILY (Sineo) | PUBLIC, WORKSPACE, FAMILY (Sineo) | creator |
| `research-crew` | PUBLIC, WORKSPACE | same | research |
| `creative-agent` | PUBLIC, WORKSPACE | same | creative |
| `voice-agent` | PUBLIC, WORKSPACE, FAMILY (delegated) | – | voice I/O |
| `installer-agent` | PUBLIC, WORKSPACE | same | bootstrap |
| `enterprise-agent` | PUBLIC, WORKSPACE | same | business |

Full table & rationale: `metadata/AGENTREGISTRY.md`.

---

## 7. Networking & access

- All services share the `kirobi-net` Docker bridge.
- Caddy terminates HTTP(S) and serves:
  - `https://kirobi.local/`        → Family PWA
  - `https://kirobi.local/api/*`   → API
  - `https://kirobi.local/auth/*`  → Auth
- mDNS broadcasts `kirobi.local` via `infra/scripts/setup-mdns.sh`.
- LAN exposure is **opt-in** via `KIROBI_BIND_HOST=0.0.0.0`.

---

## 8. Configuration model

- Source of truth: `.env` (chmod 600, gitignored).
- Template: `.env.example` (placeholders only — `AENDERE_DIESEN_*`).
- The installer rewrites every placeholder with a 48-char random secret on
  first run, then never touches it again (idempotent).
- `config/templates/` provides drop-in profile overrides for Compose, Caddy
  and Nginx so agents can scaffold new deployments without hand-editing.

---

## 9. Observability

- `kirobi-core/core-events.log` — structured agent log (append-only).
- `make logs` — live tail of all containers.
- `infra/scripts/healthcheck.sh` — synchronous probe, exit code is truth.
- `make doctor` / `python -m kirobi_core doctor` — local diagnostics.
- `.kirobi/reports/` — autonomous-iteration JSON reports.

---

## 10. Lifecycle commands

| Phase | Command |
|-------|---------|
| Install | `curl …/install.sh | bash` |
| Detect | `bash infra/scripts/detect-system.sh --json` |
| Validate env | `bash infra/scripts/validate-env.sh` |
| Start | `make up` (or `docker compose up -d`) |
| Health | `make status && bash infra/scripts/healthcheck.sh` |
| Backup | `bash infra/scripts/backup.sh` |
| Update | `bash infra/scripts/update.sh` |
| Stop | `make down` |
| Uninstall | `bash install.sh --uninstall` |

---

## 11. Extension points

- **New service:** add to `docker-compose.yml`, add a profile entry under
  `config/templates/compose/`, register in `metadata/AGENTREGISTRY.md` if it
  hosts an agent.
- **New agent:** add prompt in `prompts/`, register zone in
  `metadata/AGENTREGISTRY.md`, follow `AGENT-DECISION-MATRIX.md`.
- **New zone:** edit `metadata/ZONE-POLICY-MATRIX.md` *and*
  `metadata/SECURITY-CLASSIFICATION.md`, propagate the change through every
  Qdrant collection mapping.
- **New profile:** drop a `profile-NAME.yml` under
  `config/templates/compose/`; `install.sh --profile=NAME` will pick it up.
