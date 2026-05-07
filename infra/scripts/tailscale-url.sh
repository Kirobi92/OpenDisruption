#!/usr/bin/env bash
set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "    (tailscale CLI nicht gefunden; nutze deine Tailscale-IP oder MagicDNS manuell)"
  exit 0
fi

ts_ip="$(tailscale ip -4 2>/dev/null | head -1 || true)"
ts_name=""
status_json="$(tailscale status --json 2>/dev/null || true)"

if [ -n "$status_json" ] && command -v jq >/dev/null 2>&1; then
  ts_name="$(printf '%s' "$status_json" | jq -r '.Self.DNSName // ""' 2>/dev/null | sed 's/[.]$//' || true)"
elif [ -n "$status_json" ] && command -v python3 >/dev/null 2>&1; then
  ts_name="$(printf '%s' "$status_json" | python3 -c '
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

print(data.get("Self", {}).get("DNSName", "").rstrip("."))
' || true)"
fi

if [ -n "$ts_name" ]; then
  echo "    http://$ts_name/status                (Tailscale MagicDNS)"
fi
if [ -n "$ts_ip" ]; then
  echo "    http://$ts_ip/status                  (Tailscale IP)"
fi
if [ -z "$ts_name" ] && [ -z "$ts_ip" ]; then
  echo "    (Tailscale läuft, aber IP/MagicDNS konnte nicht ermittelt werden)"
fi
