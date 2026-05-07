#!/usr/bin/env bash

set -Eeuo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: infra/scripts/keycodi-opencode.sh [--dry-run] [--allow-cloud] [--message TEXT] [--attach URL]

Runs an opencode mission through the KeyCodi prompt template. The script refuses
to run a cloud-looking model unless --allow-cloud is explicit.

Environment:
  KEYCODI_OPENCODE_MODEL     Required for run mode, e.g. provider/model
  KEYCODI_OPENCODE_ATTACH    Optional running opencode server URL
  KEYCODI_PROMPT_FILE        Defaults to config/opencode/keycodi-agent.prompt.md
USAGE
}

dry_run=0
allow_cloud=0
message=""
attach="${KEYCODI_OPENCODE_ATTACH:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --allow-cloud)
      allow_cloud=1
      ;;
    --message)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      message="$2"
      shift
      ;;
    --attach)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      attach="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
  shift
done

if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode is not installed or not on PATH" >&2
  exit 1
fi

model="${KEYCODI_OPENCODE_MODEL:-}"
if [[ -z "$model" ]]; then
  echo "KEYCODI_OPENCODE_MODEL is required before delegating repository work to opencode" >&2
  exit 2
fi

case "$model" in
  github-copilot/*|openai/*|anthropic/*|google/*|gemini/*)
    if [[ "$allow_cloud" -ne 1 ]]; then
      echo "Refusing cloud-looking model '$model' without --allow-cloud" >&2
      exit 2
    fi
    ;;
esac

prompt_file="${KEYCODI_PROMPT_FILE:-config/opencode/keycodi-agent.prompt.md}"
if [[ ! -f "$prompt_file" ]]; then
  echo "KeyCodi prompt template not found: $prompt_file" >&2
  exit 1
fi

mission="${message:-Build the next safe OpenDisruption coding act}"
prompt="You are KeyCodi. Read ${prompt_file}, obey CLAUDE.md and AGENTS.md, then plan and execute only the approved safe slice for this mission: ${mission}"

cmd=(opencode run --agent keycodi --model "$model" --title "KeyCodi mission" --dir "$PWD")
if [[ -n "$attach" ]]; then
  cmd+=(--attach "$attach")
fi
cmd+=("$prompt")

if [[ "$dry_run" -eq 1 ]]; then
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

exec "${cmd[@]}"