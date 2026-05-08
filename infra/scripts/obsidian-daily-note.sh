#!/usr/bin/env bash
# infra/scripts/obsidian-daily-note.sh
# Legt die Daily-Note für heute im Obsidian-Vault an (idempotent).
#
# Nutzung:
#   bash infra/scripts/obsidian-daily-note.sh
#   bash infra/scripts/obsidian-daily-note.sh --dry-run
#
# Umgebungsvariablen:
#   KIROBI_VAULT_PATH   Pfad zum Vault-Root (Default: obsidian/)
#
# Zone: WORKSPACE
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
  esac
done

VAULT_PATH="${KIROBI_VAULT_PATH:-${REPO_ROOT}/obsidian}"
TODAY="$(date -u +%Y-%m-%d)"
NOTE_DIR="${VAULT_PATH}/shared-opendisruption/99-Inbox"
NOTE_FILE="${NOTE_DIR}/${TODAY}-daily.md"

if [[ -f "$NOTE_FILE" ]]; then
  echo "[obsidian-daily-note] Daily-Note bereits vorhanden: ${NOTE_FILE}"
  exit 0
fi

CONTENT="---
zone: WORKSPACE
agent: obsidian
created: ${TODAY}
updated: ${TODAY}
tags: [daily, inbox]
date: ${TODAY}
---

# Daily Note ${TODAY}

## Ziele

## Erledigte Tasks

## Notizen
"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[DRY-RUN] Würde anlegen: ${NOTE_FILE}"
  echo "--- Inhalt ---"
  echo "$CONTENT"
  exit 0
fi

mkdir -p "$NOTE_DIR"
printf '%s' "$CONTENT" > "$NOTE_FILE"
echo "[obsidian-daily-note] Angelegt: ${NOTE_FILE}"
