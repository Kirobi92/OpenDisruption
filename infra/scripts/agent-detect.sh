#!/usr/bin/env bash
# =============================================================================
# agent-detect.sh — best-effort detection of the surrounding agent runtime
# =============================================================================
# Echoes a single short identifier on stdout (one of):
#   human · cursor · claude-code · github-copilot · vscode · openai · ci · unknown
# Add --json for a richer structured payload.
# =============================================================================
set -Eeuo pipefail

JSON=0
[[ "${1:-}" == "--json" ]] && JSON=1

agent="human"
[[ -n "${CURSOR_AGENT:-}" ]]                && agent="cursor"
[[ -n "${CLAUDE_CODE:-}${CLAUDECODE:-}" ]]  && agent="claude-code"
[[ -n "${COPILOT_AGENT_ID:-}" ]]            && agent="github-copilot"
[[ -n "${OPENAI_AGENT:-}" ]]                && agent="openai"
[[ "${TERM_PROGRAM:-}" == "vscode" ]]       && agent="vscode"
[[ -n "${CI:-}${GITHUB_ACTIONS:-}" ]]       && agent="ci"

interactive="false"
[[ -t 0 && -t 1 ]] && interactive="true"

if (( JSON )); then
  cat <<EOF
{"agent":"$agent","interactive":$interactive,"term":"${TERM:-unknown}","term_program":"${TERM_PROGRAM:-unknown}","ci":"${CI:-}","github_actions":"${GITHUB_ACTIONS:-}"}
EOF
else
  printf '%s\n' "$agent"
fi
