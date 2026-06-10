# OpenDisruption Agent Instructions

This repository is the canonical sanitized OpenDisruption master.

## Boundaries

- Treat `/Datenspeicher/OpenDisruption` as source code and documentation only.
- Treat `/Datenspeicher/OpenDisruption-Data` as runtime state only. Never copy secrets,
  raw source documents, logs, databases, model files, or audit payloads into this repo.
- `OpenDisruption_Neuaufbau`, `OpenDisruption_v0.1`, `LUKI`, `LUKI Operator Orchestrator`,
  and `HERMES` are read-only fragment/reference sources unless a task explicitly says to
  migrate a named file or module.
- KIROBI/FAMILY_PRIVATE material must not mix with LUKI_BUSINESS code, prompts, evals, or
  retrieval collections.

## MVP Rule

The first shippable slice is LUKI Knowledge MVP:

- local HTTP API plus simple web UI
- local Ollama only
- Qdrant collection allowlist `luki_knowledge_v1`
- source-bound answers or explicit refusal
- audit hashes only; no plaintext questions or answers in repo logs

## Versioning

- Commit only sanitized files.
- Do not import old git history from mixed or runtime-heavy trees.
- Run tests and secret scans before pushing.
- Keep `graphify-out/` updated after code changes, but do not treat dirty graph files as
  product source.
