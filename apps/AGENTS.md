---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Apps Folder Guide

- Read order: root governance -> `apps/AGENTS.md` -> app-local README -> target app code.
- Active surfaces: `apps/web`, `apps/dashboard`, `apps/voice`.
- Frozen surfaces: `apps/mobile`, `apps/desktop`, `apps/installer` — docs, security and contract fixes only.
- UI work must follow existing auth/api/retrieval contracts before adding new surface complexity.
- New surface: `apps/web-svelte` is a SvelteKit 2 v2 graph UI served under `/v2/*` via Caddy and backed by `static/repo-graph.json`.

