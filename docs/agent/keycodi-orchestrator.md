---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-06
reviewed_by: pending
version: 1.0
---

> Audience: agents and operators who need the first active KeyCodi control surface for OpenDisruption coding work.

# KeyCodi Orchestrator

KeyCodi is the repo-owned coding orchestration layer for OpenDisruption. It sits above the existing `kirobi_core` scanner, backlog, registry and router, then prepares a governed handoff into opencode when an approved model is available.

## Active surface

```bash
python -m kirobi_core keycodi "Build the next safe OpenDisruption coding act"
python -m kirobi_core keycodi --json "Turn opencode into the coding orchestrator"
make keycodi MISSION="Turn opencode into the coding orchestrator"
```

The command produces:

- the active mission act,
- specialist delegations from `metadata/AGENTREGISTRY.md`,
- routed backlog work from the current repository scan,
- safety guardrails,
- an opencode handoff command that refuses cloud-looking models unless approval is explicit.

## Opencode bridge

```bash
KEYCODI_OPENCODE_MODEL=approved-local/model \
  bash infra/scripts/keycodi-opencode.sh --dry-run --message "Implement the approved KeyCodi slice"
```

Use `--allow-cloud` only after the mission data has been classified and cloud use has been explicitly approved for WORKSPACE data. The launcher never adds `--dangerously-skip-permissions`.

## Decision matrix excerpt

| Condition | KeyCodi decision |
|-----------|------------------|
| PUBLIC / WORKSPACE code task | Plan and route autonomously |
| FAMILY_PRIVATE / SACRED content | Stop and ask |
| Cloud-backed opencode model | Ask before sending WORKSPACE data |
| Destructive command or DB mutation | Ask before execution |
| Orphan opencode service | Treat as workbench, not source of truth |

## Recovery note

If opencode is unreachable or returns `401`, KeyCodi can still run locally through `python -m kirobi_core keycodi`. Use `opencode debug paths`, `opencode agent list`, and the dry-run launcher before changing runtime configuration.