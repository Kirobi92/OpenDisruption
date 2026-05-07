# Onboarding — for an autonomous coding agent

> Audience: any LLM-powered coding agent (Claude / GPT / Cursor / Copilot /
> Aider / Cline / Continue / …) that has just been pointed at this repo.

## Step 0 — load the system prompt

Copy [`/AGENT-SYSTEM-PROMPT.md`](../../AGENT-SYSTEM-PROMPT.md) verbatim into
your system / instructions slot.

## Step 1 — install

```bash
curl -fsSL https://raw.githubusercontent.com/Kirobi92/OpenDisruption/main/install.sh \
  | bash -s -- --auto --yes --profile=auto
```

Read `.kirobi/install.json` afterwards — it is your single source of truth
for hardware, OS, profile and the agent runtime that ran the install.

## Step 2 — orient

Run, in this order:

```bash
bash infra/scripts/detect-system.sh
bash infra/scripts/validate-env.sh
make status
```

If any of the three fails, jump to [`/AGENT-RECOVERY.md`](../../AGENT-RECOVERY.md).

## Step 3 — pick a task

When the user gives you a task:

1. Classify each affected path against the zone table
   (`AGENT-SYSTEM-PROMPT.md §1`).
2. Run the 4-axis decision check (`AGENT-DECISION-MATRIX.md §1`).
3. Execute via the appropriate verdict (ACT / ACT+LOG / ASK / REFUSE).
4. Validate with the existing test suite — never invent new tooling:
   - `python -m pytest tests/unit -q`
   - `make integration-test`
   - `docker compose config --quiet`
   - `shellcheck infra/scripts/*.sh install.sh`
5. Post the structured task summary (`AGENT-SYSTEM-PROMPT.md §8`).

## Step 4 — be a good citizen

- Never bypass the matrix to “save time”.
- Never log secrets, only their key names.
- Never send `FAMILY_PRIVATE` or `SACRED` data to an external service.
- Always write idempotent code.
- Always prefer ecosystem tooling (docker, make, pip, npm) over hand-rolled
  scripts.
- Prefer additive changes; mutate only when necessary; delete only with
  human approval.

That’s onboarding. Welcome aboard.
