---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Services Folder Guide

- Read order: root governance -> `services/AGENTS.md` -> target service README/code.
- Core priority order: `auth`, `api`, `retrieval`, `model-routing`, `ingest`, `embeddings`, `orchestrator`.
- Service changes must preserve health contracts, env determinism, and zone-aware refusals.
- Avoid undocumented cross-service coupling and duplicated auth/policy logic.

