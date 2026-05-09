---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Infra Folder Guide

- Read root governance -> `infra/AGENTS.md` -> target subfolder.
- Caddy, compose exposure, backup and host-touching scripts are security/ops sensitive.
- Keep backends private by default; Caddy remains the intended edge.
- Prefer `--dry-run` and validation before mutating host/runtime behavior.

