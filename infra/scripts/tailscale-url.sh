#!/usr/bin/env bash
set -euo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "    (tailscale CLI nicht gefunden; nutze deine Tailscale-IP oder MagicDNS manuell)"
  exit 0
fi

ts_ip="$(tailscale ip -4 2>/dev/null | head -1 || true)"
ts_name=""

if command -v python3 >/dev/null 2>&1; then
  ts_name="$(tailscale status --json 2>/dev/null | python3 - <<'PY' || true
import json
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

print(data.get("Self", {}).get("DNSName", "").rstrip("."))
PY
)"
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
