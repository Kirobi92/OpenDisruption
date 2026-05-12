#!/usr/bin/env bash
# infra/scripts/docker-disk-cleanup.sh
# Automatisches Docker Disk-Management
# Warnt bei >85%, bereinigt bei >92%
set -euo pipefail

THRESHOLD_WARN=85
THRESHOLD_CLEAN=92
TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT="${TELEGRAM_ALLOWED_USER_IDS:-1066082496}"

_tg_notify() {
    if [[ -n "$TELEGRAM_TOKEN" ]]; then
        curl -s --max-time 10 "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
            --data-urlencode "chat_id=${TELEGRAM_CHAT%%,*}" \
            --data-urlencode "text=$1" > /dev/null 2>&1 || true
    fi
}

USED_PCT=$(df / --output=pcent | tail -1 | tr -d ' %')
FREE_GB=$(df / --output=avail -BG | tail -1 | tr -d ' G')

if (( USED_PCT >= THRESHOLD_CLEAN )); then
    BEFORE=$FREE_GB
    docker system prune -f --volumes=false 2>/dev/null || true
    docker builder prune -f 2>/dev/null || true
    FREE_GB_AFTER=$(df / --output=avail -BG | tail -1 | tr -d ' G')
    FREED=$(( FREE_GB_AFTER - BEFORE ))
    _tg_notify "🧹 Auto-Disk-Cleanup: ${USED_PCT}% belegt → ${FREED}GB freigegeben. Jetzt ${FREE_GB_AFTER}GB frei."
elif (( USED_PCT >= THRESHOLD_WARN )); then
    _tg_notify "⚠️ Disk-Warnung: ${USED_PCT}% belegt (${FREE_GB}GB frei). Bald Cleanup nötig."
fi
