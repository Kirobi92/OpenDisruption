#!/usr/bin/env bash
# =============================================================================
# update.sh — safely update OpenDisruption to the latest commit + images
# =============================================================================
# Sequence:
#   1. backup (unless --no-backup)
#   2. git fetch + check fast-forward
#   3. validate compose + .env (warnings non-fatal)
#   4. docker compose pull
#   5. docker compose up -d (rolling)
#   6. healthcheck
# Flags: --dry-run --no-backup --branch=NAME --quiet --skip-validate
# =============================================================================
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

DRY=0; NO_BACKUP=0; QUIET=0; SKIP_VALIDATE=0; BRANCH=""
for a in "$@"; do
  case "$a" in
    --dry-run)        DRY=1 ;;
    --no-backup)      NO_BACKUP=1 ;;
    --quiet)          QUIET=1 ;;
    --skip-validate)  SKIP_VALIDATE=1 ;;
    --branch=*)       BRANCH="${a#*=}" ;;
    -h|--help)        sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'Unknown arg: %s\n' "$a" >&2; exit 1 ;;
  esac
done

if [[ -t 1 ]]; then G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; B=$'\e[34m'; N=$'\e[0m'
else G=""; Y=""; R=""; B=""; N=""; fi
say()  { (( QUIET )) || printf '%s▸%s %s\n' "$B" "$N" "$*"; }
ok()   { (( QUIET )) || printf '%s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s⚠%s %s\n' "$Y" "$N" "$*" >&2; }
err()  { printf '%s✖%s %s\n' "$R" "$N" "$*" >&2; }
run()  { if (( DRY )); then printf '[dry-run] %s\n' "$*"; else "$@"; fi; }

# 1. backup
if (( ! NO_BACKUP )); then
  say "creating safety snapshot"
  if [[ -x "$ROOT/infra/scripts/backup.sh" ]]; then
    run bash "$ROOT/infra/scripts/backup.sh" --quiet || warn "backup reported issues"
  fi
fi

# 2. git
if [[ -d .git ]]; then
  say "fetching git updates"
  run git fetch --tags --prune origin
  TARGET="${BRANCH:-$(git symbolic-ref --short HEAD 2>/dev/null || echo main)}"
  CURRENT="$(git rev-parse --short HEAD)"
  REMOTE="$(git rev-parse --short "origin/$TARGET" 2>/dev/null || echo "$CURRENT")"
  if [[ "$CURRENT" == "$REMOTE" ]]; then
    ok "already at origin/$TARGET ($CURRENT)"
  else
    say "fast-forwarding $TARGET: $CURRENT → $REMOTE"
    if ! run git pull --ff-only origin "$TARGET"; then
      err "non-fast-forward — resolve manually then re-run."
      exit 1
    fi
  fi
else
  warn "not a git checkout — skipping git update"
fi

# 3. validate
if (( ! SKIP_VALIDATE )); then
  say "validating docker-compose"
  if ! docker compose config --quiet; then
    err "docker-compose.yml invalid — aborting."
    exit 1
  fi
  if [[ -x "$ROOT/infra/scripts/validate-env.sh" ]]; then
    bash "$ROOT/infra/scripts/validate-env.sh" --quiet || warn "validate-env reported issues"
  fi
fi

# 4. pull images
say "pulling images"
run docker compose pull

# 5. rolling up
say "applying changes (docker compose up -d)"
run docker compose up -d --remove-orphans

# 6. healthcheck
if [[ -x "$ROOT/infra/scripts/healthcheck.sh" ]]; then
  say "running healthcheck"
  if (( DRY )); then printf '[dry-run] healthcheck.sh\n'
  elif bash "$ROOT/infra/scripts/healthcheck.sh"; then ok "healthcheck passed"
  else warn "healthcheck reported issues — see output above"; fi
fi

ok "update complete"
