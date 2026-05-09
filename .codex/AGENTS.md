# ECC for Codex CLI

This supplements the root `AGENTS.md` with a repo-local ECC baseline.

## Repo Skill

- Codex compatibility skill: `.agents/skills/OpenDisruption/SKILL.md`
- Claude compatibility skill: `.claude/skills/OpenDisruption/SKILL.md`
- Canonical verified source: `.opencode/skills/keycodi-orchestrator/SKILL.md`
- Generic lifecycle pack: `.opencode/skills/using-agent-skills/` plus the imported Agent-Skills directories under `.opencode/skills/`
- Keep user-specific credentials and private MCPs in `~/.codex/config.toml`, not in this repo.

## MCP Baseline

Treat `.codex/config.toml` as the default ECC-safe baseline for work in this repository.
The generated baseline enables GitHub, Context7, Exa, Memory, Playwright, and Sequential Thinking.

## Multi-Agent Support

- Explorer: read-only evidence gathering
- Reviewer: correctness, security, and regression review
- Docs researcher: API and release-note verification

## Workflow Files

- No dedicated workflow command files were generated for this repo.

Use these workflow files as reusable task scaffolds when the detected repository workflows recur.
