# Agent Decision Matrix

**Version:** 0.2 (Phase 0 — merged safety + routing rules)
**Zone:** WORKSPACE
**Status:** Draft for review
**Owner:** kirobi-architect
**Last Updated:** 2026-05-07

> Authoritative rules autonomous agents use to decide whether to **act**,
> **act + log**, **ask**, or **refuse**, and which KIDI/KEYBRODI rollout agent
> owns each task type. Pair this with `AGENT-SYSTEM-PROMPT.md`.

---

## Part A — Operational safety decision matrix

### A.1 The 4-axis classification

For every contemplated action, classify it on these four axes:

| Axis | Values |
|------|--------|
| **Zone** | `PUBLIC` · `WORKSPACE` · `FAMILY_PRIVATE` · `QUARANTINE` · `SACRED` |
| **Reversibility** | `reversible` (git/compose can undo) · `recoverable` (needs backup) · `irreversible` |
| **External I/O** | `none` · `outbound-public` · `outbound-private-data` |
| **Privilege** | `unprivileged` · `sudo` · `network-admin` · `data-destructive` |

The **highest** value on each axis wins. When unsure, escalate one step.

---

### A.2 The matrix

| # | Zone | Reversibility | External I/O | Privilege | Verdict | Notes |
|---|------|---------------|--------------|-----------|---------|-------|
| 1 | PUBLIC | reversible | none | unprivileged | **ACT** | silent |
| 2 | PUBLIC | reversible | outbound-public | unprivileged | **ACT + LOG** | log url + payload size |
| 3 | PUBLIC | recoverable | any | unprivileged | **ACT + LOG** | ensure backup ref in log |
| 4 | PUBLIC | irreversible | any | any | **ASK** | always |
| 5 | WORKSPACE | reversible | none | unprivileged | **ACT** | silent |
| 6 | WORKSPACE | reversible | outbound-public | unprivileged | **ACT + LOG** | – |
| 7 | WORKSPACE | reversible | outbound-private-data | unprivileged | **ASK** | might leak code/secrets |
| 8 | WORKSPACE | recoverable | any | any | **ASK** | – |
| 9 | WORKSPACE | irreversible | any | any | **ASK** | – |
| 10 | FAMILY_PRIVATE | reversible | none | unprivileged | **ACT + LOG** | local-only |
| 11 | FAMILY_PRIVATE | recoverable | none | unprivileged | **ASK** | – |
| 12 | FAMILY_PRIVATE | any | outbound-public | any | **REFUSE** | local models only |
| 13 | FAMILY_PRIVATE | any | outbound-private-data | any | **REFUSE** | – |
| 14 | FAMILY_PRIVATE | irreversible | any | any | **ASK + double-confirm** | – |
| 15 | QUARANTINE | any | any | any | **REFUSE** | move to extracts/ first after human review |
| 16 | SACRED | any | any | any | **REFUSE** unless explicit Sven OK in this session | even reads |
| 17 | any | any | any | sudo | **ASK** | always |
| 18 | any | any | any | data-destructive | **ASK + dry-run-first** | always |

`SACRED` reads with explicit approval are still allowed only via the
`kirobi-core` agent and must be logged.

---

### A.3 Inputs to the classification

#### A.3.1 Determining the zone

1. Inspect every input path against the table in `AGENT-SYSTEM-PROMPT.md` §1
   and against `metadata/ZONE-POLICY-MATRIX.md`.
2. Inspect every output path the same way.
3. Inspect file frontmatter — explicit `zone: SACRED` overrides folder.
4. Inspect Qdrant collection name — `kirobi_family*` ⇒ `FAMILY_PRIVATE`.
5. **The highest zone wins.** Defaults: unknown file = `SACRED`; web fetch =
   `PUBLIC`; user message = `WORKSPACE`.

#### A.3.2 Determining reversibility

| Reversible | Recoverable | Irreversible |
|------------|-------------|--------------|
| `git revert`, `git restore` | restore from `archive/snapshots/` or container volume | overwrites with no backup, `rm -rf`, `DROP TABLE`, `docker compose down -v`, third-party API write |

#### A.3.3 Determining external I/O

- **none**: stdin/stdout, local files, local Docker network.
- **outbound-public**: GET to a public registry/docs site, no payload.
- **outbound-private-data**: any POST/PUT to a non-localhost host, OR any
  request whose body or headers contain non-PUBLIC data.

`localhost`, `127.0.0.1`, `::1`, the `kirobi-net` Docker bridge, and
`*.kirobi.local` count as **none** (they are local).

#### A.3.4 Determining privilege

- **sudo / root**: `sudo`, `doas`, `su`, writing to `/etc`, `/usr`, `/var` or
  any system path; binding to ports < 1024 outside Caddy.
- **network-admin**: changing firewall, opening LAN ports, modifying
  `KIROBI_BIND_HOST`, editing Caddyfile to add public hostnames.
- **data-destructive**: `rm -rf`, `truncate`, `DROP`, `DELETE FROM`, schema
  migrations without down-migration, `docker compose down -v`, force-pushing.

---

### A.4 Verdict semantics

#### ACT

Execute immediately. No prompt. Still write a one-line entry in
`kirobi-core/core-events.log` if the action mutates state (file write,
container start, DB write).

#### ACT + LOG

Execute immediately, but emit a structured log entry:

```
[2026-05-06T18:35:00Z] [agent-id] INFO action=write path=extracts/workspace/x.md
  zone=WORKSPACE bytes=2048 reason="user requested summary"
```

#### ASK

Pause, present an **Action Approval Request**:

```
ACTION APPROVAL REQUEST
─────────────────────────
Intent       : <one sentence>
Files / cmd  : <exact paths or command line>
Zone         : <highest>
Reversibility: <reversible | recoverable | irreversible>
External I/O : <none | outbound-* | …>
Privilege    : <unprivileged | sudo | …>
Risk         : <low | medium | high>
Undo         : <how to undo, or "irreversible">

Approve? [y/N]
```

Only proceed on an explicit `y` from the human. Default = NO.

#### REFUSE

Politely decline. Use the templates in `AGENT-SYSTEM-PROMPT.md` §7. Do not
work around the refusal (e.g. by chunking data and sending it piecemeal).

---

### A.5 Ambiguity & escalation

When in doubt:

1. **Increase the zone one level** (PUBLIC→WORKSPACE→FAMILY→SACRED).
2. **Decrease the privilege one level** (act → ask).
3. **Prefer dry-run.** Every script must support `--dry-run`.
4. **Prefer additive over mutative.** New file > modify > delete.
5. **Prefer reversible.** Move to `archive/` instead of `rm -rf`.

If still unclear, **ASK**. Asking is always cheaper than recovering.

---

### A.6 Worked examples

| Scenario | Zone | Rev. | Ext. | Priv. | Verdict |
|----------|------|------|------|-------|---------|
| Add a markdown note to `extracts/workspace/notes/` | WORKSPACE | reversible | none | un | ACT |
| `npm install` in `apps/web` | WORKSPACE | reversible | outbound-public | un | ACT + LOG |
| Send a file from `extracts/family-private/` to OpenAI for summarisation | FAMILY | recoverable | outbound-private-data | un | **REFUSE** (use local Ollama) |
| `docker compose down -v` | WORKSPACE | irreversible | none | data-destructive | **ASK** |
| Edit `Caddyfile` to add `kids.example.com` (public hostname) | WORKSPACE | reversible | none | network-admin | **ASK** |
| Read a file under `sacred/` | SACRED | reversible | none | un | **REFUSE** unless Sven approved this session |
| Run `pytest tests/unit -q` | WORKSPACE | reversible | none | un | ACT |
| `git push` | WORKSPACE | reversible | outbound-public | un | ACT + LOG (but never push secrets) |
| Move file from `quarantine/` to `extracts/workspace/` | QUARANTINE→WORKSPACE | reversible | none | un | **ASK** (zone change requires human review) |
| Create a fresh `.env` with random secrets | WORKSPACE | reversible | none | un | ACT (idempotent — only if missing) |

---

### A.7 Logging contract

Every ACT + LOG, ASK and REFUSE must emit one line to
`kirobi-core/core-events.log`:

```
[ISO-8601] [agent-id] LEVEL key1=value1 key2="value with space" ...
```

Required keys: `action`, `zone`, `verdict`. Optional but encouraged:
`path`, `bytes`, `cmd`, `reason`, `risk`, `approver`.

Never log secret values, only their key names.

---

## Part B — KIDI/KEYBRODI task-routing matrix

### B.1 Purpose

This section is the **single source of truth** for "which agent owns which task type." `keybrodi` (see `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`) consults this table at routing time. Changes to the table are PRs, not runtime mutations.

The matrix covers only the new agents introduced by the KIDI rollout. Existing agents (`kirobi-core`, `hermes-extractor`, `samira-heart`, etc.) keep their responsibilities as defined in `metadata/AGENTREGISTRY.md`.

---

### B.2 Routing table

| Task type                                    | Primary agent       | Fallback           | Allowed zones (input)                | Allowed zones (output)              | Human approval required? |
|----------------------------------------------|---------------------|--------------------|--------------------------------------|-------------------------------------|--------------------------|
| Generate / refactor source code              | `opencode`          | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No (read), Yes (commit)  |
| Code review / lint / test authoring          | `opencode`          | `hermes-reasoner`  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| CI/CD pipeline change                        | `opencode`          | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | **Yes**                  |
| Dependency update                            | `opencode`          | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | **Yes**                  |
| Web fetch / scrape (PUBLIC URL)              | `openclaw`          | —                  | PUBLIC                               | PUBLIC, QUARANTINE (until reviewed) | No                       |
| External API call (no private data)          | `openclaw`          | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| External API call (carries any private data) | — (rejected)        | —                  | n/a                                  | n/a                                 | n/a — disallowed         |
| Local filesystem operation in PUBLIC/WORKSPACE | `openclaw`        | `opencode`         | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| Local filesystem operation in `/sacred/`     | — (rejected)        | —                  | n/a                                  | n/a                                 | n/a — disallowed         |
| Browser automation (Playwright)              | `openclaw`          | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE, QUARANTINE       | **Yes** if writing       |
| Multi-step reasoning / chain-of-thought      | `hermes-reasoner`   | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| Pro/contra debate                            | `hermes-reasoner`   | —                  | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| Hypothesis generation + validation           | `hermes-reasoner`   | `kidi`             | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| Research synthesis (multi-source)            | `hermes-reasoner`   | `kidi`             | PUBLIC, WORKSPACE                    | PUBLIC, WORKSPACE                   | No                       |
| Vault read (note retrieval)                  | `obsidian`          | —                  | PUBLIC, WORKSPACE, FAMILY_PRIVATE¹   | same as input                       | No                       |
| Vault write (new note / update)              | `obsidian`          | —                  | PUBLIC, WORKSPACE, FAMILY_PRIVATE¹   | same as input                       | No (PUBLIC/WORKSPACE), **Yes** (FAMILY_PRIVATE) |
| Vault write to `/sacred/` paths              | — (rejected)        | —                  | n/a                                  | n/a                                 | n/a — disallowed         |
| Knowledge-graph query                        | `obsidian`          | —                  | per requester max-zone               | per requester max-zone              | No                       |
| Daily-note generation                        | `obsidian`          | —                  | WORKSPACE                            | WORKSPACE                           | No                       |
| MOC (Map of Content) generation              | `obsidian`          | —                  | per requester max-zone               | per requester max-zone              | No                       |
| Cross-agent synthesis                        | `kidi`              | —                  | per inputs (zone-preserving)         | ≤ min(input zones)                  | **Yes** if any SACRED    |
| Conflict detection across agents             | `kidi`              | —                  | per inputs                           | per inputs                          | No                       |
| Task routing                                 | `keybrodi`          | —                  | n/a (metadata only)                  | n/a                                 | No                       |
| Performance metric write                     | `keybrodi`          | —                  | WORKSPACE                            | WORKSPACE                           | No                       |
| Telegram outbound message                    | `keybrodi` → gate²  | —                  | PUBLIC, WORKSPACE only               | PUBLIC, WORKSPACE only              | No (auto-rejects above)  |

¹ `obsidian` is the only new agent permitted to touch FAMILY_PRIVATE, and only against the local vault on a host with `KIROBI_EGRESS_ALLOWED=false`.
² See `docs/agent/TELEGRAM-INTEGRATION.md` — the zone gate is non-bypassable; it auto-rejects FAMILY_PRIVATE/SACRED/QUARANTINE.

---

### B.3 Tie-breaking rules

When the matrix lists a fallback:

1. Try the primary agent.
2. On `unreachable`, `timeout`, or `unsupported_subtype`, try the fallback.
3. On a second failure, return the failure to the caller. **Never** silently route to a third agent.

When the matrix lists no fallback and the primary fails, the task is rejected.

---

### B.4 Zone validation algorithm (executed by `keybrodi`)

```
def validate(task, candidate_agent):
    if task.zone not in allowed_input_zones(candidate_agent, task.type):
        return REJECT("zone not in agent's input policy")
    if task.output_zone > task.zone:                       # no escalation
        return REJECT("output zone exceeds input zone")
    if task.requires_human_approval and not task.approval_token:
        return DEFER("awaiting human approval")
    if task.destination == "telegram" and task.zone > WORKSPACE:
        return REJECT("telegram destination forbidden above WORKSPACE")
    return OK
```

---

### B.5 What is explicitly not in this matrix

- **LLM model selection** — that is `metadata/MODEL-REGISTRY.md`'s job.
- **Embedding model selection** — `metadata/COLLECTION-MAPPING.md`.
- **Per-user permissions** — `services/auth/` and `metadata/ZONE-POLICY-MATRIX.md`.
- **Storage decisions** — `metadata/COLLECTION-MAPPING.md`, `docs/agent/CONTEXT-WINDOW.md`.

This matrix answers both:

1. *May this autonomous operation proceed?*
2. *Given a typed KIDI/KEYBRODI task, which new agent runs it?*

---

## Cross-references

- `AGENT-SYSTEM-PROMPT.md`
- `docs/agent/MULTI-AGENT-ARCHITECTURE.md`
- `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`
- `docs/agent/CONTEXT-WINDOW.md`
- `docs/agent/KIDI-ENGINE.md`
- `docs/agent/TELEGRAM-INTEGRATION.md`
- `metadata/ZONE-POLICY-MATRIX.md`
- `metadata/AGENTREGISTRY.md`
- `CLAUDE.md` §5 (per-agent permissions), §17 (human-in-the-loop)
