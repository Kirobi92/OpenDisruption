---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# OpenDisruption Copilot Instructions

## Start Here
Read in this order before planning or editing:

1. `CLAUDE.md` — mandatory safety, zone, approval, and no-cloud rules.
2. `AGENTS.md` — repo operations, commands, current conventions, and canonical skill references.
3. `.opencode/skills/keycodi-orchestrator/SKILL.md` — repo-owned orchestration and current priorities.
4. `keycodi/ROADMAP.md` — strict phase order and exit criteria.
5. `keycodi/MILESTONES.md` — current gate status and remaining checklist items.
6. `keycodi/decisions/0001-phase4-kidi-keybrodi-implementation-plan.md` — current critical-path implementation detail until the dedicated execution-plan document lands.
7. `.opencode/skills/using-agent-skills/SKILL.md` — only after repo-specific docs are loaded.

## Strategic Direction: HYBRID
- Keep OpenDisruption's local-first core, filesystem-as-system-of-record model, zone security, and KeyCodi/KEYBRODI direction.
- Selectively adopt proven infrastructure instead of rewriting the repo around it:
  - `LiteLLM` for provider abstraction
  - `Temporal` and/or `LangGraph` for durable orchestration where needed
  - `Postgres RLS` plus `OpenFGA` and/or `OPA` for authorization/policy
  - `Langfuse` and `OpenLIT` for observability
- Prefer incremental integration behind stable web/api contracts. Do not replace working core architecture just to match external frameworks.

## Frozen / Deprioritized
- Freeze net-new feature work in `apps/mobile/`, `apps/desktop/`, and `apps/installer/`.
- Only allow:
  - essential fixes,
  - security work,
  - contract-alignment changes,
  - or documentation updates.
- Do not expand these apps until core web/api contracts are solid and a later phase/spec explicitly re-opens them.

## Skill Selection Rules
Use this precedence order:

1. `CLAUDE.md`
2. `AGENTS.md`
3. repo-specific skills under `.opencode/skills/` (`keycodi-orchestrator`, `kirobi-*`)
4. the dedicated execution-plan document when present
5. imported generic lifecycle skills under `.opencode/skills/`

Rules:
- Imported lifecycle skills are additive workflow helpers, not repo policy.
- If a generic lifecycle skill conflicts with repo docs or repo-specific skills, follow the repo-specific source.
- Treat compatibility mirrors under `.agents/skills/` or `.claude/skills/` as mirrors, not the primary authority.

## Phase Gates
- Follow `keycodi/ROADMAP.md` phase order strictly. Do not invent a parallel track because it feels convenient.
- Use `keycodi/MILESTONES.md` as the readiness gate before advancing.
- Current critical path: complete CI hygiene for earlier phases and Phase 4 (`KIDI + KEYBRODI`) before satellite work.
- `Phase 5 (Telegram)` remains gated until Phases 1-4 are green and local Docker secrets exist.
- Frozen clients stay frozen until web/api contracts are stable.
- If a requested task conflicts with the current phase order or gate state, document the conflict and stop rather than improvising a new sequence.

## Where the Detailed Execution Plan Lives
- The detailed execution plan belongs in the dedicated execution-plan document for this repo once that document exists.
- Until then, use this stack together:
  - `keycodi/ROADMAP.md` for sequencing
  - `keycodi/MILESTONES.md` for gate status
  - `keycodi/decisions/0001-phase4-kidi-keybrodi-implementation-plan.md` for the current critical-path implementation detail
- Do not create ad hoc replacement plans in unrelated docs.
