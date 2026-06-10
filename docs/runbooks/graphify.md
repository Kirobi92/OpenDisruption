# Graphify Runbook

Graphify is a first-class OpenDisruption knowledge plane.

## Commands

```bash
graphify query "LUKI Knowledge MVP policy graphify"
graphify explain "LUKI Knowledge MVP"
graphify path "LUKI Knowledge MVP" "Graphify"
graphify update .
python3 tools/opendisruption_ultimate.py graph --json
```

## Runtime Surfaces

- CLI status: `python3 tools/opendisruption_ultimate.py graph --json`
- MVP API: `GET /api/graphify`
- UI card: `Graphify` shows `<nodes>/<edges>`
- Files: `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`

## Rules

- Run `graphify query` before broad architecture or codebase decisions when
  `graphify-out/graph.json` exists.
- Run `graphify update .` after code changes.
- Dirty `graphify-out/` files are expected after updates.
- Do not feed runtime data, secrets, logs, DB dumps, or raw private source docs
  into Graphify.
- Treat Graphify as navigation and evidence, not as a replacement for tests,
  secret scans, or policy gates.
