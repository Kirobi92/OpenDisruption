---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Integrations Folder Guide

- Treat third-party integrations as adapters, not policy authorities.
- Keep root zone/security rules in force; no private-data egress without approval.
- Reuse central auth/model/telemetry contracts instead of embedding bespoke logic per integration.

