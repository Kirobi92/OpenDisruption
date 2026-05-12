#!/usr/bin/env bash
# Installiert den Kirobi Nightly Consolidation Systemd-Timer.
# Muss als root oder mit sudo ausgeführt werden.
# Usage: sudo bash infra/scripts/install-nightly-timer.sh [--dry-run]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

run() {
    if $DRY_RUN; then
        echo "[DRY-RUN] $*"
    else
        "$@"
    fi
}

echo "=== Kirobi Nightly Timer Installation ==="
echo "Repo: $REPO_ROOT"
echo "DRY-RUN: $DRY_RUN"
echo ""

# Prüfen ob systemd vorhanden
if ! systemctl --version &>/dev/null; then
    echo "FEHLER: systemd nicht verfügbar. Nutze stattdessen cron:"
    echo "  crontab -e"
    echo "  0 2 * * * bash $REPO_ROOT/infra/scripts/nightly-consolidation.sh"
    exit 1
fi

# Service und Timer kopieren
run cp "$REPO_ROOT/infra/systemd/kirobi-nightly.service" /etc/systemd/system/
run cp "$REPO_ROOT/infra/systemd/kirobi-nightly.timer" /etc/systemd/system/

# Systemd neu laden
run systemctl daemon-reload

# Timer aktivieren und starten
run systemctl enable kirobi-nightly.timer
run systemctl start kirobi-nightly.timer

if ! $DRY_RUN; then
    echo ""
    echo "✅ Timer aktiv:"
    systemctl status kirobi-nightly.timer --no-pager || true
    echo ""
    echo "Nächste Ausführung:"
    systemctl list-timers kirobi-nightly.timer --no-pager || true
    echo ""
    echo "Manuell testen:"
    echo "  sudo systemctl start kirobi-nightly.service"
    echo "  journalctl -u kirobi-nightly.service -f"
fi
