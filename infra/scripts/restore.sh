#!/usr/bin/env bash
# =============================================================================
# restore.sh — restore a Kirobi snapshot tarball produced by backup.sh
# =============================================================================
# Usage:
#   restore.sh --from=<tarball> [--dry-run] [--target=<dir>] [--no-db] [--no-vectors]
#
# Defaults to validating the snapshot integrity only (--dry-run). To actually
# restore data, pass --apply. Existing files in target paths are NOT overwritten
# unless --force is passed.
# =============================================================================
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC=""
TARGET="$ROOT"
DRY=1            # default: validation only
FORCE=0
DO_DB=1
DO_VEC=1
QUIET=0

for a in "$@"; do
  case "$a" in
    --from=*)     SRC="${a#*=}" ;;
    --target=*)   TARGET="${a#*=}" ;;
    --apply)      DRY=0 ;;
    --dry-run)    DRY=1 ;;
    --force)      FORCE=1 ;;
    --no-db)      DO_DB=0 ;;
    --no-vectors) DO_VEC=0 ;;
    --quiet)      QUIET=1 ;;
    -h|--help)    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)            printf 'Unknown arg: %s\n' "$a" >&2; exit 1 ;;
  esac
done

log()  { (( QUIET )) || printf '▸ %s\n' "$*"; }
warn() { printf '⚠ %s\n' "$*" >&2; }
err()  { printf '✗ %s\n' "$*" >&2; exit 1; }

[ -n "$SRC" ] || err "Missing --from=<tarball>"
[ -f "$SRC" ] || err "Snapshot not found: $SRC"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

log "Validating archive: $SRC"
tar -tzf "$SRC" >/dev/null || err "Archive corrupted"

log "Extracting to staging area"
tar -xzf "$SRC" -C "$WORK"

# locate inner snapshot dir (backup.sh wraps content in TIMESTAMP folder)
INNER="$(find "$WORK" -mindepth 1 -maxdepth 1 -type d | head -1)"
[ -d "$INNER" ] || err "Snapshot has no top-level directory"

log "Snapshot contents:"
ls -la "$INNER" | sed 's/^/   /'

# Pre-flight zone safety
for zone in canon experiences extracts sacred; do
  if [ -d "$INNER/$zone" ]; then
    log "  zone present: $zone ($(du -sh "$INNER/$zone" | cut -f1))"
  fi
done

if [ -f "$INNER/postgres.sql.gz" ]; then
  log "  postgres dump: $(du -h "$INNER/postgres.sql.gz" | cut -f1)"
fi

if [ -d "$INNER/qdrant" ]; then
  log "  qdrant snapshots: $(find "$INNER/qdrant" -maxdepth 2 -type f | wc -l) file(s)"
fi

if (( DRY )); then
  log "✓ Dry-run validation passed. Re-run with --apply to actually restore."
  exit 0
fi

log "APPLY MODE: restoring zones to $TARGET"
for zone in canon experiences extracts sacred; do
  [ -d "$INNER/$zone" ] || continue
  if [ -d "$TARGET/$zone" ] && (( ! FORCE )); then
    warn "  $zone exists, skipping (use --force to overwrite)"
    continue
  fi
  log "  restoring $zone"
  cp -a "$INNER/$zone" "$TARGET/"
done

if (( DO_DB )) && [ -f "$INNER/postgres.sql.gz" ]; then
  log "Restoring Postgres (requires running postgres container)"
  if docker compose ps postgres --status running --quiet | grep -q .; then
    gunzip -c "$INNER/postgres.sql.gz" | \
      docker compose exec -T postgres psql -U "${POSTGRES_USER:-kirobi}" -d "${POSTGRES_DB:-kirobi}"
  else
    warn "  postgres not running — skipping DB restore"
  fi
fi

if (( DO_VEC )) && [ -d "$INNER/qdrant" ]; then
  warn "Qdrant snapshot restore is manual: copy $INNER/qdrant/* into qdrant_data volume,"
  warn "then call /collections/<name>/snapshots/<file>/recover via Qdrant API."
fi

log "✓ Restore complete."
