---
zone: WORKSPACE
created_by: copilot-cli
created_at: 2026-05-09
reviewed_by: pending
version: "1.0"
---

# Next-Generation Execution Plan for OpenDisruption

## Executive decision: evolve, do not rewrite

**Decision:** evolve the current repository and runtime in-place; **do not create a hard fork or greenfield rewrite** of the platform.

Why:
- the repo already contains the right local-first, zone-aware and service-oriented shape;
- the biggest risks are missing contracts, weak gates and surface sprawl, not missing ideas;
- a rewrite would reset hard-won security/governance context while preserving the same uncertainty.

**Upstream strategy:** adopt upstream components **selectively behind stable internal contracts**. Upstream is allowed to replace implementation detail, not the repo's security model, file-system-of-record principle or agent governance.

**Last-resort fork rule:** only fork an upstream dependency if all three are true: (1) blocking bug or missing local-first/privacy feature, (2) adapter/wrapper is insufficient, (3) patch delta can stay small and test-covered.

---

## How autonomous agents must execute this plan

1. **Run phases strictly in order.** No later phase starts before the current phase gate passes.
2. **Treat gates as hard stops.** If a phase fails verification, stop, document the blocker, and work only on rollback or remediation inside the same phase.
3. **Prefer contract-first changes.** No new feature work before interface, schema and ownership are explicit.
4. **Keep the file system as source of truth.** Postgres/Qdrant/workflow state remain derived or recoverable.
5. **Respect zone controls.** Use `CLAUDE.md`, `metadata/ZONE-POLICY-MATRIX.md`, `SECURITY.md` and `THREAT-MODEL.md` as non-negotiable constraints.
6. **Produce evidence per phase.** Each gate must leave behind executable proof: tests, validation output, docs, and rollback notes.

Primary references:
- [`PROJECT-ARCHITECTURE.md`](../PROJECT-ARCHITECTURE.md)
- [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- [`DEVELOPER-RUNBOOK.md`](../DEVELOPER-RUNBOOK.md)
- [`SECURITY.md`](../SECURITY.md)
- [`THREAT-MODEL.md`](../THREAT-MODEL.md)
- [`ROADMAP.md`](../ROADMAP.md)
- [`AGENTS.md`](../AGENTS.md)

---

## GitHub execution model

This plan is intended to be executed on GitHub as a strict backlog, not as loose prose.

### Board structure

- **Epic:** one phase or one cross-cutting platform track
- **Issue:** one deliverable with a single verification target
- **PR:** one coherent implementation slice

### Recommended labels

- `phase:0` … `phase:6`
- `area:auth`, `area:api`, `area:retrieval`, `area:ingest`, `area:web`, `area:dashboard`, `area:infra`, `area:keycodi`
- `type:feature`, `type:fix`, `type:docs`, `type:test`, `type:infra`, `type:security`
- `gate:blocker`, `gate:ready`, `gate:passed`
- `zone:workspace`, `zone:public`

### Issue template contract

Each implementation issue should contain:

1. **Goal**
2. **Scope in / out**
3. **Files / services touched**
4. **Verification command**
5. **Definition of done**
6. **Rollback note**

### Milestone model

- Milestone = one phase gate
- Close milestone only when every exit criterion in this document and `keycodi/MILESTONES.md` is satisfied

---

## Current baseline and immediate truth

This plan assumes the repo has a strong architecture/governance base but still has execution gaps.

**Current verified gate:** `make integration-test` now passes in the local repo environment.

Implication:
- Phase 0 evidence can now rely on the repo gate again, but future phase work must keep it green.

---

## Freeze, deprecation and risk posture

### Immediate freeze until Phase 3 passes

**Feature freeze:** no net-new end-user features in these surfaces until architecture, contracts and CI gates are stable:
- `apps/desktop/`
- `apps/mobile/`
- `apps/installer/`
- `services/image-generation/`
- `services/media-processing/`
- `services/music-generation/`
- `services/video-generation/`
- `services/telegram/` beyond break/fix and security fixes

**Workflow freeze:** Flowise may remain for prototyping and human-visible experimentation, but **must not become the only production control plane** for critical long-running workflows.

**Customization freeze:** avoid large UX rewrites in `apps/web/` and `apps/dashboard/` until contracts and authz boundaries are stable.

### Deprecation direction

Deprecate over time:
- direct service-to-model calls that bypass a single routing/gateway contract;
- ad-hoc JSON payloads without versioned schemas;
- long-running business logic encoded only in Flowise graphs;
- duplicated authorization checks scattered independently across services and frontends.

### Migration-risk truth

Highest-risk migrations:
1. auth/authz enforcement changes;
2. model-routing/gateway insertion;
3. workflow-runtime replacement for durable execution;
4. observability instrumentation that changes request paths or payloads.

Rule: migrations in these areas require shadow mode, contract tests and rollback steps before cutover.

---

## Product-surface priority order

| Priority | Surface | Decision | Notes |
|---|---|---|---|
| P0 | `services/auth`, `services/api`, `services/retrieval`, `services/model-routing`, `apps/web`, `apps/dashboard` | invest now | core trust, interaction and system control surface |
| P1 | `services/ingest`, `services/embeddings`, `services/orchestrator`, `kirobi_core/`, `kirobi-core/` | stabilize next | platform backbone and autonomous execution |
| P2 | `services/voice-processing`, `apps/voice` | limited progress | only after contracts/authz/gates exist |
| P3 | `services/telegram` | keep narrow | adapter only, no strategic expansion now |
| P4 | media/gen surfaces and desktop/mobile/installer scaffolds | freeze | no platform-scale investment before P0/P1 are green |

**Interpretation:** OpenDisruption becomes credible by hardening its core platform and primary web surface first; the rest stays intentionally secondary until the platform is trustworthy.

---

## Sequential gated phases

---

## Phase 0 - Baseline, inventory and freeze enforcement

**Goal:** establish a truthful starting point and prevent more architectural drift.

### Required inputs
- [`DEVELOPER-RUNBOOK.md`](../DEVELOPER-RUNBOOK.md)
- [`PROJECT-ARCHITECTURE.md`](../PROJECT-ARCHITECTURE.md)
- [`SECURITY.md`](../SECURITY.md)
- [`THREAT-MODEL.md`](../THREAT-MODEL.md)

### Execution steps
1. Run and record baseline commands:
   - `python -m pytest tests/unit -q`
   - `make integration-test`
   - `docker compose config --quiet`
   - `bash infra/scripts/validate-env.sh`
   - `python -m kirobi_core doctor`
2. Create a platform inventory for:
   - service boundaries;
   - externally reachable endpoints;
   - workflow entry points;
   - current schema owners;
   - current model call paths.
3. Mark frozen surfaces explicitly in planning/backlog artifacts.
4. Identify every place where one service depends on another service's internal shape rather than a documented contract.
5. Identify all long-running tasks currently handled by ad-hoc code or Flowise-only state.

### Verification gate
- baseline command results are captured and reproducible;
- every P0/P1 surface has a named owner and explicit boundary;
- frozen surfaces are documented and not receiving new strategic scope.

### Stop conditions
- baseline commands cannot be reproduced reliably;
- service ownership is ambiguous;
- critical workflows cannot be enumerated.

### Rollback / containment
- no strategic code moves yet;
- revert any accidental freeze-scope changes;
- keep work limited to inventory and baseline remediation.

**Only proceed if Phase 0 gate passes.**

---

## Phase 1 - Architecture hardening

**Goal:** reduce platform fragility before introducing more dependencies or features.

### Focus areas
- runtime boundaries;
- failure isolation;
- idempotent service startup;
- zone enforcement at service boundaries;
- dependency hygiene.

### Execution steps
1. Define the canonical runtime path for one primary request:
   - user -> web -> auth/api -> model-routing -> model provider(s) -> retrieval/ingest as needed.
2. Remove or fence any bypass path that skips the intended core path for P0 surfaces.
3. Make startup/bootstrap contracts explicit for `auth`, `api`, `retrieval`, `model-routing`, `ingest`, `embeddings`, `orchestrator`.
4. Ensure every service has:
   - health endpoint or equivalent check;
   - deterministic env requirements;
   - documented failure mode;
   - explicit persistence expectation.
5. Align service responsibilities with [`PROJECT-ARCHITECTURE.md`](../PROJECT-ARCHITECTURE.md); if reality differs, update code or docs so one truth exists.
6. Fix baseline dependency drift exposed in Phase 0 so local and CI environments can execute the same checks.

### Verification gate
- primary request path is documented and enforced;
- no P0 service relies on undocumented startup side effects;
- health/doctor output covers every P0/P1 service;
- baseline checks no longer fail due to missing undeclared runtime/test dependencies.

### Stop conditions
- architecture requires simultaneous multi-service rewrites to stay coherent;
- a P0 surface cannot expose a stable health contract;
- zone enforcement is still impossible to verify at boundary level.

### Rollback / containment
- keep old path behind a feature flag or adapter until the hardened path passes smoke tests;
- if a service split increases instability, revert to prior boundary and re-document the decision.

**Only proceed if Phase 1 gate passes.**

---

## Phase 2 - Contract stabilization

**Goal:** make the core platform testable and replaceable by stabilizing interfaces before major adoption work.

### Contracts that must exist
1. **API contracts:** auth, chat/query, retrieval, ingest, workflow/task submission, health/status.
2. **Event contracts:** audit events, job lifecycle events, model invocation events.
3. **Schema contracts:** Postgres tables used across services, file metadata, Qdrant collection metadata.
4. **Policy contracts:** zone checks, authn/authz decisions, external-egress approval rules.
5. **Adapter contracts:** upstream gateway, workflow engine, observability pipeline.

### Execution steps
1. Version every shared contract that crosses service boundaries.
2. Add contract tests for request/response shape and failure semantics.
3. Define compatibility rules:
   - additive changes allowed behind versioning;
   - breaking changes require migration notes and rollback path;
   - internal-only fields must not leak across boundaries.
4. Standardize error envelopes and audit/event naming.
5. Make model-routing the only supported abstraction point for model-provider calls on P0 surfaces.
6. Define a stable workflow submission contract even if the durable runtime is not yet chosen.
7. Define a stable authorization decision interface even if the authz engine is not yet chosen.

### Verification gate
- every P0/P1 boundary has a versioned contract or schema reference;
- contract tests fail on breaking changes;
- model access and authz checks can be swapped behind adapters without changing callers.

### Stop conditions
- cross-service changes still require editing unrelated consumers blindly;
- no versioning policy is accepted in practice;
- P0 surfaces still expose undocumented or shape-shifting payloads.

### Rollback / containment
- keep v1 contracts live until v2 passes shadow/compatibility checks;
- use translation adapters instead of hard cutovers when possible.

**Only proceed if Phase 2 gate passes.**

---

## Phase 3 - CI, policy gates and release discipline

**Goal:** make regressions harder than progress.

### Required repo-local gates
- `python -m pytest tests/unit -q`
- `make integration-test`
- `docker compose config --quiet`
- `bash infra/scripts/validate-env.sh`
- `bash install.sh --dry-run --no-clone --auto --skip-checks --no-pull --no-models --no-start --profile=cpu`

### Execution steps
1. Make the baseline commands deterministic on contributor machines and in CI.
2. Wire them into GitHub Actions without duplicating incompatible logic.
3. Add phase-appropriate blockers:
   - contract tests for P0/P1 surfaces;
   - zone-enforcement tests for sensitive boundaries;
   - installer/compose validation;
   - schema migration checks where applicable.
4. Establish branch/PR merge criteria:
   - no merge on red baseline;
   - no merge on contract break without migration note;
   - no merge on new external dependency without justification.
5. Add artifact retention for logs and failure evidence.
6. Make CI output point contributors back to the canonical commands in [`DEVELOPER-RUNBOOK.md`](../DEVELOPER-RUNBOOK.md).

### Verification gate
- CI reproduces local required gates;
- a deliberate contract break fails CI;
- a deliberate zone-policy violation is caught by tests;
- installer dry run remains green for supported profiles.

### Stop conditions
- local and CI results diverge materially;
- gate failures are noisy but not actionable;
- merge policy can be bypassed accidentally.

### Rollback / containment
- if a new CI step is flaky, quarantine it behind non-blocking status until stabilized;
- do not weaken existing gates to land strategic features.

**Only proceed if Phase 3 gate passes.**

---

## Phase 4 - Selective upstream adoption behind adapters

**Goal:** bring in upstream leverage only where the core is now strong enough to contain it.

### 4A. LiteLLM (model gateway)

**Intent:** standardize provider access, routing policy and fallback behavior without scattering provider logic.

**Adopt if:**
- model-routing contract is stable;
- P0 callers already depend on internal gateway interfaces rather than raw provider payloads.

**Pilot steps**
1. Put LiteLLM behind the existing model-routing boundary, not directly in callers.
2. Shadow one non-critical path first.
3. Compare latency, fallback behavior, provider parity and auditability.
4. Keep direct local path available until parity is proven.

**Verification**
- equal or better behavior for local-first routing;
- no zone-policy regression;
- request/response/audit fields map cleanly to internal contracts.

**Stop if**
- local Ollama behavior becomes second-class;
- auditability worsens;
- adapter code becomes more complex than the old gateway.

**Rollback**
- switch traffic back to current model-routing implementation via adapter flag.

### 4B. Durable workflows

**Intent:** move critical long-running execution out of brittle in-memory/ad-hoc/Flowise-only state.

**Decision rule:** adopt a durable runtime for production-critical workflows, but keep Flowise as optional prototype UX.

**Pilot steps**
1. Identify one workflow with retries, pause/resume and audit needs.
2. Implement it behind a stable workflow submission contract.
3. Run in shadow mode alongside existing behavior.
4. Prove replay, retry, timeout and operator visibility.

**Verification**
- workflow survives process restart;
- job state is queryable and auditable;
- retries are deterministic enough for operator trust.

**Stop if**
- operator burden exceeds current simplicity;
- runtime forces cloud-first assumptions;
- migration demands broad caller rewrites.

**Rollback**
- revert that workflow to current orchestrator/DB-backed execution path; keep contract intact.

### 4C. Authz

**Intent:** centralize authorization decisions instead of duplicating them across services.

**Adopt if:**
- authn flow in `services/auth` is already stable;
- zone policy and service policy boundaries are expressible through one decision interface.

**Pilot steps**
1. Define a single authorization decision API for `subject`, `action`, `resource`, `zone`, `context`.
2. Enforce it first on P0 surfaces only.
3. Back it with an upstream policy engine or service only through an adapter.
4. Add deny-by-default tests and audit events.

**Verification**
- authorization logic is no longer duplicated in P0 services;
- deny-by-default behavior is test-covered;
- policy decisions are logged without leaking sensitive payloads.

**Stop if**
- authz engine adds a new unbounded operational dependency;
- policy expression cannot represent zone rules clearly;
- latency or availability of authz blocks core flows.

**Rollback**
- fall back to current service-local enforcement while preserving the decision interface.

### 4D. Observability

**Intent:** add real traces/metrics/log correlation without coupling business logic to a vendor.

**Adopt if:**
- event names and primary request path are already stable.

**Pilot steps**
1. Standardize correlation IDs across auth/api/model-routing/retrieval/orchestrator.
2. Instrument request, job and model spans behind an internal telemetry adapter.
3. Keep `kirobi-core/core-events.log` as the canonical local audit trail.
4. Add dashboards only for P0/P1 services first.

**Verification**
- one request can be followed across the core path;
- telemetry does not leak forbidden-zone data;
- operators can answer latency/error questions without code spelunking.

**Stop if**
- telemetry adds privacy risk or material runtime overhead;
- observability stack becomes mandatory for local development.

**Rollback**
- disable exporter path, keep local logs and health checks.

**Only proceed if all selected Phase 4 pilots either pass or are explicitly rejected with recorded reasons.**

---

## Phase 5 - Product-surface concentration and migration

**Goal:** converge the repo around the surfaces that should represent the next-generation product.

### Execution steps
1. Promote P0 surfaces as the canonical product path:
   - `apps/web` as primary user surface;
   - `apps/dashboard` as operator/admin surface;
   - `services/auth`, `api`, `retrieval`, `model-routing` as core platform services.
2. Keep P1 services only if they serve P0 paths with stable contracts.
3. Keep P2/P3/P4 surfaces in one of three states only:
   - frozen scaffold;
   - experimental adapter;
   - supported product surface.
4. Remove ambiguous “kind of supported” status from docs and backlog.
5. Update docs so the canonical path is obvious to humans and agents.

### Verification gate
- repo docs consistently point to one primary product path;
- frozen surfaces are clearly marked;
- unsupported surfaces no longer appear as equal-priority roadmap promises.

### Stop conditions
- more than one competing primary UX/control plane remains;
- migration leaves users without an operator-visible path for the core use case.

### Rollback / containment
- restore previous docs/feature flags if the primary surface is not yet functionally complete;
- do not delete frozen scaffolds until at least one release cycle proves they are truly unnecessary.

**Only proceed if Phase 5 gate passes.**

---

## Phase 6 - Cutover, deprecation execution and steady-state evolution

**Goal:** finish the transition without pretending migration risk is over.

### Execution steps
1. Cut over one capability at a time: gateway, workflow runtime, authz, observability.
2. Keep old and new paths measurable during transition.
3. Mark deprecated paths with end-of-support criteria, not vague intent.
4. Remove dead code only after:
   - replacement is live;
   - rollback window expires;
   - CI has covered the new path for at least one full release cycle.
5. Convert this plan into a rolling operating cadence: quarterly architecture review, monthly contract review, continuous gate maintenance.

### Verification gate
- deprecated paths are either removed or time-boxed with owners;
- rollback instructions remain valid;
- steady-state platform metrics exist for core latency, failure rate and policy denials.

### Stop conditions
- cutover requires “big bang” migration;
- operators cannot revert within a bounded window;
- deprecation removes fallback before replacement is trusted.

### Rollback / containment
- route traffic back through prior adapter/feature flag;
- restore prior contract version for callers;
- keep migration data reversible wherever possible.

---

## What success looks like

The next-generation strategy is successful when all of the following are true:
- OpenDisruption has **one hardened primary platform path**;
- core services are **contract-stable and CI-gated**;
- upstream components are **replaceable implementations, not architectural owners**;
- authz, workflow durability and observability are **centralized and testable**;
- frozen surfaces are honest about status;
- roadmap promises match what the repo can actually operate.

---

## Repo command appendix

Use these commands as the canonical execution and verification set:

```bash
python -m pytest tests/unit -q
make integration-test
docker compose config --quiet
bash infra/scripts/validate-env.sh
python -m kirobi_core doctor
python -m kirobi_core doctor --live
python -m kirobi_core status --json
bash install.sh --dry-run --no-clone --auto --skip-checks --no-pull --no-models --no-start --profile=cpu
```

Useful supporting references:
- [`README.md`](../README.md)
- [`DEVELOPER-RUNBOOK.md`](../DEVELOPER-RUNBOOK.md)
- [`PROJECT-ARCHITECTURE.md`](../PROJECT-ARCHITECTURE.md)
- [`SECURITY.md`](../SECURITY.md)
- [`THREAT-MODEL.md`](../THREAT-MODEL.md)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)

---

## Agent completion checklist per phase

A phase is complete only when:
- the execution steps are done;
- the verification gate is green;
- stop conditions are explicitly checked and not triggered;
- rollback steps were written or tested;
- docs and commands still point to the same reality.

If any item is false, the phase is not complete.
