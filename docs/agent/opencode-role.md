---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-06
reviewed_by: pending
version: 1.0
---

> Audience: agents and operators who notice a running `kirobi-opencode` service and need to decide whether to use, ignore, or shut it down.

# Opencode Role

## KeyCodi promotion

OpenDisruption now treats `KeyCodi - Master-Code-Orchestrator` as the repo-owned coding orchestration layer. `opencode` is the workbench KeyCodi may delegate into, after local safety preflight and explicit model approval.

Start with:

```bash
python -m kirobi_core keycodi "Turn opencode into the coding orchestrator"
```

Then use `infra/scripts/keycodi-opencode.sh --dry-run` before any real opencode run.

## Recommended role

`opencode` should be treated as KeyCodi's governed coding workbench, not as the authority that decides repository policy by itself.

Its best fit in OpenDisruption is:

- quick UI-level experimentation,
- scratchpad prompting against local Ollama,
- ad-hoc browser access on `http://127.0.0.1:4096` or `http://opencode.local`,
- non-authoritative comparison against the primary repo agent.

## Why this matters

The currently running container is compose-adjacent and may appear as an orphan in `docker compose` output. Its runtime configuration mixes:

- local model connectivity via `OLLAMA_HOST=http://ollama:11434`, and
- a cloud-oriented default model via `OPENCODE_MODEL=github-copilot/gpt-5.5`.

That means `opencode` is not automatically safe to treat as a local-only agent for WORKSPACE data.

## Operating rule

Use `opencode` only when all three conditions hold:

1. The task is non-sensitive WORKSPACE work.
2. You do not need it to be the source of truth for repo changes.
3. Cloud-backed model usage has been explicitly approved for the task.

If any of those conditions are false, prefer `python -m kirobi_core keycodi` plus the local Docker/PWA surfaces instead.

## Practical guidance

- If `docker compose ps` shows `kirobi-opencode` as an orphan, do not assume it belongs to the active profile.
- If you want to keep it, document its profile and ownership first.
- If you want to integrate it more deeply, define a local-only model path before giving it broader repository responsibilities.
- If it is only causing noise, leave it alone unless a human explicitly asks for cleanup; orphan removal changes runtime state.