#!/usr/bin/env bash
# infra/scripts/obsidian-moc-generator.sh
# Generiert/aktualisiert den Map-of-Content (00-Index.md) für alle oder einen Agenten.
#
# Nutzung:
#   bash infra/scripts/obsidian-moc-generator.sh                  # alle Agenten
#   bash infra/scripts/obsidian-moc-generator.sh --agent opencode # ein Agent
#   bash infra/scripts/obsidian-moc-generator.sh --dry-run        # nur ausgeben
#
# Umgebungsvariablen:
#   KIROBI_VAULT_PATH   Pfad zum Vault-Root (Default: obsidian/)
#
# Zone: WORKSPACE
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DRY_RUN=false
AGENT_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --agent)   AGENT_FILTER="${2:-}"; shift 2 ;;
    *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
  esac
done

VAULT_PATH="${KIROBI_VAULT_PATH:-${REPO_ROOT}/obsidian}"
AGENTS_DIR="${VAULT_PATH}/agents"
TODAY="$(date -u +%Y-%m-%d)"

if [[ ! -d "$AGENTS_DIR" ]]; then
  echo "[obsidian-moc] Agenten-Verzeichnis nicht gefunden: ${AGENTS_DIR}" >&2
  exit 1
fi

# Agenten-Liste bestimmen
if [[ -n "$AGENT_FILTER" ]]; then
  AGENT_DIRS=("${AGENTS_DIR}/${AGENT_FILTER}")
else
  mapfile -t AGENT_DIRS < <(find "$AGENTS_DIR" -mindepth 1 -maxdepth 1 -type d | sort)
fi

generate_moc() {
  local agent_dir="$1"
  local agent_name
  agent_name="$(basename "$agent_dir")"
  local moc_file="${agent_dir}/00-Index.md"

  # Alle Notes ausser 00-Index.md
  local notes=()
  while IFS= read -r -d '' f; do
    notes+=("$(basename "$f")")
  done < <(find "$agent_dir" -maxdepth 1 -name '*.md' ! -name '00-Index.md' -print0 | sort -z)

  local content
  content="---
zone: WORKSPACE
agent: obsidian
created: ${TODAY}
updated: ${TODAY}
tags: [moc, index]
---

# ${agent_name} — Vault Map of Content

_Automatisch generiert von obsidian-moc-generator.sh am ${TODAY}_

## Notes

"
  if [[ ${#notes[@]} -gt 0 ]]; then
    for note in "${notes[@]}"; do
      local stem="${note%.md}"
      content+="- [[${stem}]]\n"
    done
  else
    content+="_noch keine Notes_\n"
  fi

  content+="
## Verweise

- [[../../shared-opendisruption/00-Index/MOC|Shared OpenDisruption MOC]]
- [[../../../keycodi/ROADMAP|KeyCodi Roadmap]]
"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] MOC für '${agent_name}': ${moc_file}"
    printf '%b' "$content"
    echo "---"
    return
  fi

  mkdir -p "$agent_dir"
  printf '%b' "$content" > "$moc_file"
  echo "[obsidian-moc] Aktualisiert: ${moc_file}"
}

for dir in "${AGENT_DIRS[@]}"; do
  if [[ ! -d "$dir" ]]; then
    echo "[obsidian-moc] WARNUNG: Verzeichnis nicht gefunden: ${dir}" >&2
    continue
  fi
  generate_moc "$dir"
done

echo "[obsidian-moc] Fertig."
