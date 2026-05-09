---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Tests Folder Guide

- Read root governance -> `tests/AGENTS.md` -> target test suite.
- `make integration-test` is the repo gate.
- Keep tests aligned with documented contracts; prefer regression tests for any behavior change.
- Use stdlib-first compatibility where possible; avoid making the baseline heavier than necessary.

