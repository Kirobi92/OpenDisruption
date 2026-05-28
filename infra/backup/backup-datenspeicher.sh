#!/bin/bash
# =============================================================================
# Kirobi Backup Script — Täglicher verschlüsselter Backup /Datenspeicher
# OPE-100 | Agent: Kirobi | Erstellt: 2026-05-20
# =============================================================================

set -euo pipefail

# Lade ENV — 2026-05-28 Phase C: migriert von .backup.env nach secrets/restic.env
ENV_FILE="/Datenspeicher/OpenDisruption-Data/secrets/restic.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Backup-ENV nicht gefunden: $ENV_FILE"
    exit 1
fi
set -a
source "$ENV_FILE"
set +a

LOG_FILE="/Datenspeicher/OpenDisruption-Data/shared/logs/backup.log"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-1066082496}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[${TIMESTAMP}] $*" | tee -a "$LOG_FILE"
}

send_telegram() {
    local msg="$1"
    if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${msg}" \
            -d "parse_mode=Markdown" > /dev/null 2>&1 || true
    fi
}

mkdir -p "$(dirname "$LOG_FILE")"

log "=== Backup gestartet ==="

# Ausschluesse: große Binaries, Caches, temporäre Dateien
# Live-DB-Volumes ausgeschlossen — werden separat via mysqldump/pg_dumpall in db-dumps/ gesichert
EXCLUDES=(
    --exclude "/Datenspeicher/Backups"
    --exclude "*.tmp"
    --exclude "*.log.backup"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/models"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/ComfyUI/models"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/ComfyUI/output"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/data/webshop-mysql"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/data/webshop-postgres"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/data/partdb-db"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sineo/agent/disabled-hermes-profiles"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/Benutzer-Ordner/Sven/Projekte/hermes-web-ui/hermes_data"
    --exclude "node_modules"
    --exclude ".git"
    --exclude "__pycache__"
    --exclude "*.pyc"
    --exclude "/Datenspeicher/OpenDisruption_v0.1/docker-volumes"
)

# Pre-Backup: DB-Dumps frisch erzeugen (Konsistenz)
DUMP_DIR="/Datenspeicher/OpenDisruption-Data/backups/db-dumps/daily"
mkdir -p "$DUMP_DIR"
log "Erstelle DB-Dumps..."
docker exec webshop-mysql sh -c 'mysqldump --single-transaction --routines --triggers --events --all-databases -uroot -p"$MYSQL_ROOT_PASSWORD"' 2>/dev/null | gzip > "$DUMP_DIR/webshop-mysql.sql.gz" || log "WARN: webshop-mysql dump failed"
docker exec webshop-postgres sh -c 'pg_dumpall -U "$POSTGRES_USER"' 2>/dev/null | gzip > "$DUMP_DIR/webshop-postgres.sql.gz" || log "WARN: webshop-postgres dump failed"
docker exec partdb-db sh -c 'mysqldump --single-transaction --routines --triggers --events --all-databases -uroot -p"$MYSQL_ROOT_PASSWORD"' 2>/dev/null | gzip > "$DUMP_DIR/partdb-mysql.sql.gz" || log "WARN: partdb-db dump failed"

log "Starte restic backup..."
# restic exit codes: 0=clean, 1=warnings (e.g. unreadable files), 3=warnings (newer versions).
# Wir akzeptieren 1+3 als Erfolg, wenn ein Snapshot erstellt wurde.
set +e
restic backup /Datenspeicher/OpenDisruption_v0.1 \
    "${EXCLUDES[@]}" \
    --tag "kirobi-daily" \
    --tag "$(date '+%Y-%m-%d')" \
    2>&1 | tee -a "$LOG_FILE"
RESTIC_EXIT=${PIPESTATUS[0]}
set -e

# Snapshot wurde gespeichert wenn "snapshot ... saved" in log
if grep -q "snapshot .* saved" "$LOG_FILE" 2>/dev/null && [[ "$RESTIC_EXIT" -le 3 ]]; then
    
    log "Backup erfolgreich abgeschlossen."
    
    # Alte Snapshots rotieren: behalte 7 täglich, 4 wöchentlich, 3 monatlich
    log "Rotiere alte Snapshots..."
    restic forget \
        --keep-daily 7 \
        --keep-weekly 4 \
        --keep-monthly 3 \
        --prune \
        2>&1 | tee -a "$LOG_FILE"
    
    # Snapshot-Info
    SNAPSHOT_COUNT=$(restic snapshots --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "?")
    REPO_SIZE=$(du -sh /Datenspeicher/Backups/restic-repo 2>/dev/null | cut -f1 || echo "?")
    
    log "Snapshots gesamt: ${SNAPSHOT_COUNT} | Repo-Größe: ${REPO_SIZE}"
    
    send_telegram "✅ *Kirobi Backup erfolgreich*
📅 ${TIMESTAMP}
📦 Snapshots: ${SNAPSHOT_COUNT}
💾 Repo-Größe: ${REPO_SIZE}
🔒 Verschlüsselt: AES-256 (restic)"
    
else
    log "ERROR: Backup fehlgeschlagen!"
    send_telegram "❌ *Kirobi Backup FEHLGESCHLAGEN*
📅 ${TIMESTAMP}
🔍 Prüfe: ${LOG_FILE}"
    exit 1
fi

log "=== Backup abgeschlossen ==="
