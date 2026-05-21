#!/usr/bin/env bash
# Obsidian → APK Graph Auto-Sync
# Täglich 02:00 via systemd-Timer ausgeführt.
# Baut vault-graph.json + repo-graph.json neu und kopiert sie in APK-Graph-Endpunkte.
# OPE-117 | Erstellt von Kirobi CEO Agent 2026-05-20
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_VAULT="$REPO_ROOT/infra/scripts/build-vault-graph.py"
SCRIPT_REPO="$REPO_ROOT/infra/scripts/build-repo-graph.py"
LOG_DIR="$REPO_ROOT/infra/logs"
LOG_FILE="$LOG_DIR/obsidian-graph-export.log"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Obsidian Graph Export gestartet ==="

# Python-Interpreter ermitteln
PYTHON=""
for candidate in \
    "$REPO_ROOT/.venv/bin/python3" \
    /usr/local/bin/python3 \
    /usr/bin/python3 \
    python3; do
    if command -v "$candidate" &>/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    log "FEHLER: Python3 nicht gefunden"
    exit 1
fi

# 1. Vault-Graph bauen → apps/web/public/graph.json
VAULT_OUT="$REPO_ROOT/apps/web/public/graph.json"
log "Baue Vault-Graph → $VAULT_OUT"
"$PYTHON" "$SCRIPT_VAULT" --output "$VAULT_OUT" 2>&1 | tee -a "$LOG_FILE" || {
    log "FEHLER: build-vault-graph.py fehlgeschlagen (Exit: $?)"
}

# 2. Repo-Graph bauen → apps/web-svelte/static/repo-graph.json
REPO_OUT="$REPO_ROOT/apps/web-svelte/static/repo-graph.json"
log "Baue Repo-Graph → $REPO_OUT"
"$PYTHON" "$SCRIPT_REPO" --output "$REPO_OUT" 2>&1 | tee -a "$LOG_FILE" || {
    log "FEHLER: build-repo-graph.py fehlgeschlagen (Exit: $?)"
}

# 3. Kopie in apps/web/public/repo-graph.json (Next.js Web-App)
if [[ -f "$REPO_OUT" ]]; then
    cp "$REPO_OUT" "$REPO_ROOT/apps/web/public/repo-graph.json"
    log "Kopiert: repo-graph.json → apps/web/public/"
fi

# 4. APK public-Ordner aktualisieren (wenn vorhanden)
APK_WEB_DIR="$REPO_ROOT/apps/web-svelte/build/client"
if [[ -d "$APK_WEB_DIR" ]]; then
    cp "$REPO_OUT" "$APK_WEB_DIR/v2/repo-graph.json" 2>/dev/null || true
    log "APK Build-Verzeichnis aktualisiert: $APK_WEB_DIR/v2/repo-graph.json"
fi

# 5. Graph-Nodes zählen und loggen
if [[ -f "$VAULT_OUT" ]]; then
    NODE_COUNT=$(python3 -c "import json; d=json.load(open('$VAULT_OUT')); print(d['meta']['node_count'])" 2>/dev/null || echo "?")
    LINK_COUNT=$(python3 -c "import json; d=json.load(open('$VAULT_OUT')); print(d['meta']['link_count'])" 2>/dev/null || echo "?")
    log "Vault-Graph: $NODE_COUNT Nodes, $LINK_COUNT Links"
fi

log "=== Obsidian Graph Export abgeschlossen ==="
