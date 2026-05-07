# KEYBRODI — Master Orchestrator

**Version:** 0.1 (Phase 0 — design only)
**Zone:** WORKSPACE
**Status:** Draft for review
**Owner:** kirobi-architect
**Last Updated:** 2026-05-06

---

## 1. Scope

KEYBRODI is the **task router and metric collector** for the KIDI rollout. It is intentionally less ambitious than the original problem statement, which described an "emergent superintelligence." This document defines what KEYBRODI is in this codebase: a deterministic, auditable, human-reviewable orchestrator.

**KEYBRODI is:**
- A routing function: `(task, zone, context) -> agent`.
- A metric writer: latency, success/failure, agent choice → `kirobi-core/core-events.log`.
- A policy enforcer: rejects routes that would violate `ZONE-POLICY-MATRIX.md`.

**KEYBRODI is not:**
- A self-modifying program. Any change to its routing table is a PR.
- A model. It does not invoke an LLM to decide routing in Phase 4 — the routing table is static and lives in `AGENT-DECISION-MATRIX.md`.
- A new policy authority. It calls into the existing zone-permission checks; it does not reimplement them.

---

## 2. Routing contract

```
route(task) -> RoutingDecision {
    agent:        "opencode" | "openclaw" | "hermes-reasoner" | "obsidian" | "kidi",
    zone:         <task zone, validated against agent permissions>,
    rationale:    "<why this agent — table cell from AGENT-DECISION-MATRIX.md>",
    fallback:     <next agent in priority list, or null>,
    requires_human_approval: bool
}
```

Routing is driven by the table in `AGENT-DECISION-MATRIX.md`. KEYBRODI's only job at the routing step is:

1. Look up the task type in the matrix.
2. Verify the candidate agent is permitted in the task's zone (cross-check with `ZONE-POLICY-MATRIX.md`).
3. Mark `requires_human_approval=true` for any high-risk action defined in `CLAUDE.md` §17.
4. Return the decision; do **not** execute.

Execution is the caller's responsibility. This separation keeps KEYBRODI testable and auditable.

---

## 3. Metric collection

For every routed task, KEYBRODI appends a line to `kirobi-core/core-events.log`:

```
[<ISO-8601>] [keybrodi] ROUTE task_id=<uuid> agent=<name> zone=<zone> latency_ms=<n> outcome=<success|failure|deferred>
```

For every KIDI synthesis it triggers:

```
[<ISO-8601>] [keybrodi] SYNTHESIZE task_id=<uuid> inputs=<n> output_zone=<zone> confidence=<f>
```

These are **observability only**. They do not feed back into routing in this rollout.

---

## 4. What "self-optimization" means here

The original problem statement called for reinforcement learning that mutates orchestrator behavior. That is explicitly out of scope per `CLAUDE.md` §17 ("ALWAYS REQUIRE APPROVAL: … Modifying security policies, … Adding new agents").

In this rollout, "self-optimization" reduces to:

1. **Metric collection** (above).
2. **Surfacing metrics** in a dashboard (Phase 6, optional).
3. **Human-authored routing-table edits** based on those metrics, via PR.

No code path exists where KEYBRODI rewrites `AGENT-DECISION-MATRIX.md` or its in-memory routing table at runtime.

---

## 5. Predictive orchestration (deferred)

The "predictive orchestration" described in the problem statement (proactively planning next steps) requires either:

- a planner LLM with broad zone access — currently incompatible with `CLAUDE.md` §3 for FAMILY_PRIVATE/SACRED, or
- a hand-curated workflow library.

The hand-curated path is the only safe option and is deferred to a later proposal. Phase 4 ships only reactive routing.

---

## 6. Zone enforcement at the orchestrator boundary

KEYBRODI rejects, before any agent is invoked:

- A task whose payload contains FAMILY_PRIVATE/SACRED data and whose target agent is not permitted to read that zone.
- A task whose target output zone is **higher** than its input zone (no escalation).
- A task that names a Telegram bot as the destination but contains a payload tagged above WORKSPACE (see `TELEGRAM-INTEGRATION.md`).

All rejections are logged with reason codes:

```
[<ISO-8601>] [keybrodi] REJECT task_id=<uuid> reason=ZONE_PERMISSION agent=<name> zone=<zone>
```

---

## 7. Failure modes

| Scenario                                  | Behavior                                              |
|-------------------------------------------|-------------------------------------------------------|
| Routing table missing entry for task type | Reject with `UNKNOWN_TASK_TYPE`                       |
| Agent unreachable                         | Try fallback if defined; else reject                  |
| ContextDB write fails                     | Reject; do not silently lose the metric               |
| Human approval required but not present   | Defer: queue task and notify via the configured channel |

---

## 8. Cross-references

- `AGENT-DECISION-MATRIX.md` — the routing table KEYBRODI consults
- `docs/agent/MULTI-AGENT-ARCHITECTURE.md` — overall topology
- `docs/agent/KIDI-ENGINE.md` — synthesis layer KEYBRODI may invoke
- `metadata/ZONE-POLICY-MATRIX.md` — authoritative zone permissions
- `CLAUDE.md` §5, §6, §17 — agent permissions, high-risk paths, human-in-the-loop
