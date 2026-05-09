#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

ts_host="${KIROBI_TAILSCALE_HOST:-}"
kirobi_host="${KIROBI_HOSTNAME:-kirobi.local}"

if [ -z "$ts_host" ] && command -v tailscale >/dev/null 2>&1; then
  status_json="$(tailscale status --json 2>/dev/null || true)"
  if [ -n "$status_json" ]; then
    if command -v jq >/dev/null 2>&1; then
      ts_host="$(printf '%s' "$status_json" | jq -r '.Self.DNSName // ""' 2>/dev/null | sed 's/[.]$//' || true)"
    else
      ts_host="$(STATUS_JSON="$status_json" python3 - <<'PY'
import json
import os

try:
    data = json.loads(os.environ["STATUS_JSON"])
except Exception:
    raise SystemExit(0)

print((data.get("Self", {}).get("DNSName", "") or "").rstrip("."))
PY
)"
    fi

    if [ -z "$ts_host" ]; then
      ts_host="$(tailscale ip -4 2>/dev/null | head -1 || true)"
    fi
  fi
fi

if [ -z "$ts_host" ]; then
  echo "Keine Tailscale-Adresse erkannt."
  echo "Verbinde den Host zuerst mit: sudo tailscale up --ssh"
  exit 0
fi

base_url="http://$ts_host"

cat <<EOF
OpenDisruption via Tailscale
Base URL: $base_url
Fallback local hostname: http://$kirobi_host

User surfaces
  $base_url/                         Family PWA Start
  $base_url/status                   MVP Status
  $base_url/chat                     Zone-aware Chat
  $base_url/search                   Suche / RAG
  $base_url/upload                   Upload / Ingest
  $base_url/settings                 Account / Permissions

Operator surfaces
  $base_url/dashboard/               Admin Dashboard
  $base_url/dashboard/tasks          Tasks / Human gates
  $base_url/dashboard/services       Service-Status
  $base_url/dashboard/agents         Agenten-Ansicht

Workbench surfaces (LAN/Tailscale only)
  $base_url/open-webui/              Open WebUI
  $base_url/flowise/                 Flowise
  $base_url/qdrant/dashboard         Qdrant Dashboard

Service endpoints
  $base_url/api/health               API Health
  $base_url/api/control/status       Operator Control Status
  $base_url/api/tasks                Task Feed
  $base_url/api/analytics/stats      Analytics Stats
  $base_url/voice/health             Voice Service Health

Best use
  1. Lass alle Backend-Ports auf 127.0.0.1 und nutze nur Caddy als Edge.
  2. Verwende MagicDNS statt roher IP, sobald der Host im Tailnet sauber registriert ist.
  3. Nutze Tailscale SSH fuer Admin-Zugriff; kein Router-Portforwarding, kein Funnel.
EOF
