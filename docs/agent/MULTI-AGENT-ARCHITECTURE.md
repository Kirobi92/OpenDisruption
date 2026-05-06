# Multi-Agent Architecture (KIDI / KEYBRODI Rollout)

**Version:** 0.1 (Phase 0 — design only)
**Zone:** WORKSPACE
**Status:** Draft for review
**Owner:** kirobi-architect
**Last Updated:** 2026-05-06

---

## 1. Purpose

This document defines the target architecture for the KIDI (Kollektive Integrale Disruptive Intelligenz) rollout — a multi-agent layer composed of OpenCode, OpenClaw, Hermes-Reasoner, Obsidian, and a KEYBRODI master orchestrator that emerges from their collective output.

It is the **architectural contract** that all subsequent phases (1–6) must satisfy. No runtime code is shipped in this PR.

---

## 2. Hard Constraints (non-negotiable)

These constraints derive directly from `/CLAUDE.md` and `metadata/ZONE-POLICY-MATRIX.md`. Any phase that violates them must be rejected in review.

1. **No FAMILY_PRIVATE / SACRED / QUARANTINE data leaves the host.** This explicitly applies to Telegram, which is treated as an external service (see `TELEGRAM-INTEGRATION.md`).
2. **No parallel vector store.** Embeddings reuse the seven Qdrant collections defined in `metadata/COLLECTION-MAPPING.md`. No Chroma, no second Qdrant instance, no in-process FAISS for production paths.
3. **No new policy authority.** Zone permissions live in `metadata/ZONE-POLICY-MATRIX.md`. Agents enforce, they do not redefine.
4. **No `curl … | bash` without checksum + `--dry-run` default.** Any installer that breaks this rule is out of scope.
5. **No unsupervised self-modifying loop.** "Self-optimization" in this rollout is metric collection only; orchestrator changes require a human PR.
6. **Default-off for all new services.** New compose entries ship behind a profile (`--profile kidi`) and are disabled in the default `docker compose up` path.

---

## 3. Component Map

### 3.1 New agents (this rollout)

| Agent             | Role                                       | Default zones (R / W)                    | Runs as              |
|-------------------|--------------------------------------------|------------------------------------------|----------------------|
| `opencode`        | Coding, refactoring, CI/CD authoring       | PUBLIC, WORKSPACE / PUBLIC, WORKSPACE    | Container, on-demand |
| `openclaw`        | Tool-use (web, API, fs, automation)        | PUBLIC, WORKSPACE, QUARANTINE / PUBLIC, WORKSPACE, QUARANTINE | Container, on-demand |
| `hermes-reasoner` | Multi-step reasoning, debate, synthesis    | PUBLIC, WORKSPACE / PUBLIC, WORKSPACE    | Container, on-demand |
| `obsidian`        | Vault CRUD, knowledge graph, MOCs          | PUBLIC, WORKSPACE, FAMILY_PRIVATE (local-only) / same | Container, long-running |
| `kidi`            | Cross-agent synthesis, emergent insights   | PUBLIC, WORKSPACE / PUBLIC, WORKSPACE    | Library + sidecar    |
| `keybrodi`        | Master orchestrator, task router, metrics  | All (read-only for FAMILY_PRIVATE, summary form) / PUBLIC, WORKSPACE | Library + sidecar    |

> The existing `hermes-extractor` is a separate agent (ingestion). The new `hermes-reasoner` is named explicitly to avoid collision; it does **not** replace the extractor.

### 3.2 Reuse of existing surface (do not duplicate)

| Concern                | Existing component                          | What we reuse                                   |
|------------------------|---------------------------------------------|-------------------------------------------------|
| Orchestration / policy | `kirobi_core/`, `kirobi-core/`              | Routing primitives, event log, policy hooks     |
| Auth / users           | `services/auth/`                            | Token issuance, zone-permission checks          |
| Vector store           | Qdrant + `metadata/COLLECTION-MAPPING.md`   | All seven collections; KIDI writes nowhere else |
| Reverse proxy          | Caddy (`infra/caddy/Caddyfile`)             | All new HTTP endpoints terminate here           |
| Bootstrap              | `infra/scripts/bootstrap.sh`, `Makefile`    | New phases extend, never replace                |
| Tests                  | `tests/unit/` (stdlib + pytest)             | Same harness; `python -m pytest tests/unit -q`  |
| Networking             | `${KIROBI_BIND_HOST:-127.0.0.1}` convention | Every new compose port follows it               |

### 3.3 New infrastructure (single new dependency)

| Service                | Purpose                                | Bound to                              |
|------------------------|----------------------------------------|---------------------------------------|
| Redis (ContextDB)      | Shared, zone-tagged context window     | `${KIROBI_BIND_HOST:-127.0.0.1}:6379` |

No other new infra. Embedding stays on the existing Qdrant + the existing local embedding models (see `metadata/MODEL-REGISTRY.md`).

---

## 4. Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                         keybrodi (orchestrator)                  │
│   - Task router        - Metric collector       - Event logger   │
└───────────────┬──────────────────────────────────────────────────┘
                │ (in-process or local-IPC; never over WAN)
        ┌───────┴───────┬──────────────┬───────────────┐
        ▼               ▼              ▼               ▼
   opencode        openclaw      hermes-reasoner   obsidian
        │               │              │               │
        └───────┬───────┴──────────────┴───────────────┘
                ▼
         ContextDB (Redis)  ──►  KIDI synthesis  ──►  Qdrant collections
                                                       (existing, reused)
```

Optional, opt-in:

```
keybrodi ──► Telegram zone-gate ──► Telegram bots (PUBLIC/WORKSPACE only)
```

The Telegram path is **off by default** and gated by `KIROBI_TELEGRAM_ENABLED=false` in `.env.example`. See `TELEGRAM-INTEGRATION.md`.

---

## 5. Lifecycle of a Task

1. Caller submits a task (CLI, HTTP, or scheduled job) to `keybrodi`.
2. `keybrodi` consults the routing table in `AGENT-DECISION-MATRIX.md` and zone permissions in `ZONE-POLICY-MATRIX.md`.
3. Selected agent reads any required prior context from ContextDB **scoped to the task's zone**.
4. Agent executes; result is written back to ContextDB with `{agent, zone, timestamp, payload, confidence}`.
5. KIDI may aggregate multiple ContextDB entries into a synthesis entry (same zone or downgraded with logging).
6. `keybrodi` records metrics (latency, success, agent choice) to `kirobi-core/core-events.log`.
7. Optional: Obsidian agent persists a Markdown note for any entry whose zone permits it.
8. Optional: Telegram bot publishes a summary, after passing the zone gate.

---

## 6. Phasing (recap)

| Phase | Scope                                                   | This PR? |
|-------|---------------------------------------------------------|----------|
| 0     | Architecture docs + zone matrix update                  | ✅ yes   |
| 1     | ContextDB (Redis) + Python API + tests                  | no       |
| 2     | Agent skeletons + base class + Makefile targets         | no       |
| 3     | Obsidian vault + Qdrant reuse                           | no       |
| 4     | KIDI synthesis + KEYBRODI router (metrics-only)         | no       |
| 5     | Telegram (only after policy sign-off — see §2)          | no       |
| 6     | `install.sh`, README/Benutzerhandbuch updates           | no       |

---

## 7. Open Questions (must be answered before Phase 5)

1. **Telegram policy.** Confirm: hard zone gate to PUBLIC/WORKSPACE only? Or drop Telegram entirely in favor of a local chat UI?
2. **Token storage.** If Telegram proceeds: env file (encrypted at rest), Docker secret, or external secret manager?
3. **Cron defaults.** Daily team meeting: opt-in (default off) is the proposal — confirm.
4. **`install.sh` distribution.** Repo-local script (run from clone) is the proposal — confirm `curl | bash` is not required.

---

## 8. Cross-references

- `docs/agent/CONTEXT-WINDOW.md` — Redis schema, zone tagging
- `docs/agent/KIDI-ENGINE.md` — synthesis algorithm, Qdrant reuse
- `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md` — orchestrator design
- `docs/agent/TELEGRAM-INTEGRATION.md` — zone gate, opt-in
- `AGENT-DECISION-MATRIX.md` — task routing
- `metadata/ZONE-POLICY-MATRIX.md` — authoritative permissions
- `metadata/COLLECTION-MAPPING.md` — Qdrant collections (reused)
- `CLAUDE.md` — operational constraints (mandatory)
