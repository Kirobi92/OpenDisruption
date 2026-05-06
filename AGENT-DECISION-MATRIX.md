# Agent Decision Matrix

**Version:** 0.1 (Phase 0 — design only)
**Zone:** WORKSPACE
**Status:** Draft for review
**Owner:** kirobi-architect
**Last Updated:** 2026-05-06

---

## 1. Purpose

This file is the **single source of truth** for "which agent owns which task type." `keybrodi` (see `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`) consults this table at routing time. Changes to the table are PRs, not runtime mutations.

The matrix covers only the new agents introduced by the KIDI rollout. Existing agents (`kirobi-core`, `hermes-extractor`, `samira-heart`, etc.) keep their responsibilities as defined in `metadata/AGENTREGISTRY.md`.

---

## 2. Routing table

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

## 3. Tie-breaking rules

When the matrix lists a fallback:

1. Try the primary agent.
2. On `unreachable`, `timeout`, or `unsupported_subtype`, try the fallback.
3. On a second failure, return the failure to the caller. **Never** silently route to a third agent.

When the matrix lists no fallback and the primary fails, the task is rejected.

---

## 4. Zone validation algorithm (executed by `keybrodi`)

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

## 5. What is explicitly not in this matrix

- **LLM model selection** — that is `metadata/MODEL-REGISTRY.md`'s job.
- **Embedding model selection** — `metadata/COLLECTION-MAPPING.md`.
- **Per-user permissions** — `services/auth/` and `metadata/ZONE-POLICY-MATRIX.md`.
- **Storage decisions** — `metadata/COLLECTION-MAPPING.md`, `docs/agent/CONTEXT-WINDOW.md`.

This matrix only answers: *given a typed task, which new agent runs it?*

---

## 6. Cross-references

- `docs/agent/MULTI-AGENT-ARCHITECTURE.md`
- `docs/agent/KEYBRODI-SUPERINTELLIGENZ.md`
- `docs/agent/CONTEXT-WINDOW.md`
- `docs/agent/KIDI-ENGINE.md`
- `docs/agent/TELEGRAM-INTEGRATION.md`
- `metadata/ZONE-POLICY-MATRIX.md`
- `metadata/AGENTREGISTRY.md`
- `CLAUDE.md` §5 (per-agent permissions), §17 (human-in-the-loop)
