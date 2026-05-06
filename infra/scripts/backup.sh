#!/usr/bin/env bash
# =============================================================================
# backup.sh — snapshot the Kirobi data plane to a tarball under archive/snapshots
# =============================================================================
# Backs up:
#   - canon/, experiences/, extracts/, sacred/ (file system zones)
#   - Postgres logical dump (pg_dumpall)
#   - Qdrant snapshots via the snapshot API
#   - .env (chmod 600 inside the tarball)
# Skips: docker volumes raw bytes (use `docker run --rm -v ...` if needed),
#        models/ (huge, re-downloadable), node_modules/, .git/
# Flags: --dry-run --quiet --out=PATH --no-db --no-vectors
# =============================================================================
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR_DEFAULT="$ROOT/archive/snapshots"
OUT_DIR="$OUT_DIR_DEFAULT"
DRY=0; QUIET=0; DO_DB=1; DO_VEC=1

for a in "$@"; do
  case "$a" in
    --dry-run)    DRY=1 ;;
    --quiet)      QUIET=1 ;;
    --no-db)      DO_DB=0 ;;
    --no-vectors) DO_VEC=0 ;;
    --out=*)      OUT_DIR="${a#*=}" ;;
    -h|--help)    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'Unknown arg: %s\n' "$a" >&2; exit 1 ;;
  esac
done

log()  { (( QUIET )) || printf '▸ %s\n' "$*"; }
warn() { printf '⚠ %s\n' "$*" >&2; }
run()  { if (( DRY )); then printf '[dry-run] %s\n' "$*"; else "$@"; fi; }

mkdir -p "$OUT_DIR"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

ARCHIVE_NAME="kirobi-backup-$TIMESTAMP.tar.gz"
ARCHIVE_PATH="$OUT_DIR/$ARCHIVE_NAME"
log "destination: $ARCHIVE_PATH"

# 1. file zones
log "snapshotting file zones (canon, experiences, extracts, sacred)"
mkdir -p "$WORK/files"
for dir in canon experiences extracts sacred; do
  if [[ -d "$ROOT/$dir" ]]; then
    run cp -aR "$ROOT/$dir" "$WORK/files/$dir"
  fi
done

# 2. .env
if [[ -f "$ROOT/.env" ]]; then
  log "snapshotting .env"
  run cp "$ROOT/.env" "$WORK/env"
  (( DRY )) || chmod 600 "$WORK/env"
fi

# 3. Postgres
if (( DO_DB )); then
  if docker compose --project-directory "$ROOT" ps --status=running postgres 2>/dev/null | grep -q postgres; then
    log "dumping postgres → postgres.sql.gz"
    if (( DRY )); then
      printf '[dry-run] docker compose exec postgres pg_dumpall -U $POSTGRES_USER\n'
    else
      docker compose --project-directory "$ROOT" exec -T postgres \
        sh -c 'pg_dumpall -U "${POSTGRES_USER:-kirobi}"' \
        | gzip -c > "$WORK/postgres.sql.gz" \
        || warn "pg_dumpall failed — continuing without DB dump"
    fi
  else
    warn "postgres container not running — skipping DB dump"
  fi
fi

# 4. Qdrant snapshots — POST to create, then GET to actually download the
#    snapshot artifact. Without the GET we'd only ship metadata, not vectors.
if (( DO_VEC )); then
  if curl -fsS http://127.0.0.1:6333/collections >/dev/null 2>&1; then
    log "asking Qdrant for snapshots"
    mkdir -p "$WORK/qdrant"
    for col in $(curl -fsS http://127.0.0.1:6333/collections \
        | grep -oE '"name":"[^"]+"' | cut -d'"' -f4); do
      log "  · $col"
      if (( DRY )); then
        printf '[dry-run] curl POST /collections/%s/snapshots → GET snapshot file\n' "$col"
        continue
      fi
      meta="$(curl -fsS --write-out '\nHTTP %{http_code}\n' \
              -X POST "http://127.0.0.1:6333/collections/$col/snapshots" 2>&1)" \
        || { warn "qdrant snapshot create for $col failed: ${meta##*$'\n'}"; continue; }
      # Strip the trailing 'HTTP nnn' marker before persisting / parsing.
      meta="${meta%$'\nHTTP '*}"
      printf '%s' "$meta" >"$WORK/qdrant/${col}.meta.json"
      # Snapshot name is the most recently reported one for this collection.
      snap_name="$(printf '%s' "$meta" | grep -oE '"name":"[^"]+"' | head -n1 | cut -d'"' -f4)"
      if [[ -z "$snap_name" ]]; then
        warn "could not parse snapshot name for $col"
        continue
      fi
      curl -fsS "http://127.0.0.1:6333/collections/$col/snapshots/$snap_name" \
        -o "$WORK/qdrant/${col}-${snap_name}" \
        || warn "qdrant snapshot download for $col failed"
    done
  else
    warn "qdrant not reachable on 127.0.0.1:6333 — skipping vector snapshots"
  fi
fi

# 5. tar everything
log "creating tarball"
if (( DRY )); then
  printf '[dry-run] tar -czf %s -C %s .\n' "$ARCHIVE_PATH" "$WORK"
else
  tar -czf "$ARCHIVE_PATH" -C "$WORK" . \
    && chmod 600 "$ARCHIVE_PATH"
  SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
  log "✔ wrote $ARCHIVE_PATH ($SIZE)"
fi

# 6. retention — keep last 14 by default
RETAIN="${KIROBI_BACKUP_KEEP:-14}"
if (( DRY == 0 )); then
  mapfile -t OLD < <(ls -1t "$OUT_DIR"/kirobi-backup-*.tar.gz 2>/dev/null | tail -n +"$((RETAIN+1))" || true)
  for f in "${OLD[@]:-}"; do [[ -n "$f" ]] && { log "pruning $f"; rm -f "$f"; }; done
fi

log "done."
