---
zone: WORKSPACE
created_by: GitHub Copilot
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# Agents Folder Guide

- Read order: root `CLAUDE.md` -> root `AGENTS.md` -> `.github/copilot-instructions.md` -> `agents/AGENTS.md`.
- Scope: agent runtimes and shared base classes only.
- Start with `agents/_base/agent.py`, then the target agent directory.
- Preserve zone refusals and headless-safe behavior; do not add cloud-only assumptions here.
- Current focus order: `opencode`, `openclaw`, `hermes`, `obsidian`; keep implementations aligned with `keycodi/ROADMAP.md`.

