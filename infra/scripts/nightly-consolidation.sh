#!/usr/bin/env bash
# Kirobi Nightly Consolidation — Shell-Wrapper
# Wird von systemd oder cron aufgerufen.
# Aktiviert das Python-venv und führt das Hauptskript aus.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO_ROOT/infra/scripts/nightly-consolidation.py"
LOG_DIR="$REPO_ROOT/infra/logs"
LOG_FILE="$LOG_DIR/nightly-consolidation.log"

mkdir -p "$LOG_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nightly Consolidation gestartet" >> "$LOG_FILE"

# Python-Interpreter ermitteln
PYTHON=""
for candidate in \
    "$REPO_ROOT/.venv/bin/python3" \
    /usr/local/bin/python3 \
    /usr/bin/python3 \
    python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FEHLER: Python3 nicht gefunden" >> "$LOG_FILE"
    exit 1
fi

# Env-Datei laden (Passwörter, Tokens)
if [[ -f "$REPO_ROOT/.env" ]]; then
    # Nur sichere KEY=VALUE-Zeilen laden
    set -a
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Z_]+=.+$' "$REPO_ROOT/.env" | grep -v '#') 2>/dev/null || true
    set +a
fi

export REPO_ROOT

# Skript ausführen, Ausgabe in Logfile und stdout
"$PYTHON" "$SCRIPT" "$@" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE="${PIPESTATUS[0]}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nightly Consolidation beendet (Exit: $EXIT_CODE)" >> "$LOG_FILE"
exit "$EXIT_CODE"
