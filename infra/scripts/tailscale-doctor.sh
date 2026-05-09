#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v tailscale >/dev/null 2>&1; then
  echo "tailscale_status=missing"
  echo "hint=Installiere Tailscale hostweit und verbinde dann genau diesen Rechner mit deinem Tailnet."
  exit 0
fi

echo "tailscale_status=installed"
echo "tailscale_version=$(tailscale version | head -1)"

status_json="$(tailscale status --json 2>/dev/null || true)"
if [ -z "$status_json" ]; then
  echo "backend_state=unknown"
  echo "hint=Der Host ist noch nicht mit dem Tailnet verbunden oder tailscaled antwortet nicht."
  echo "next_step=sudo tailscale up --ssh"
  exit 0
fi

STATUS_JSON="$status_json" python3 - <<'PY'
import json
import os

data = json.loads(os.environ["STATUS_JSON"])
self = data.get("Self") or {}

tailscale_ips = ",".join(self.get("TailscaleIPs") or [])
dns_name = (self.get("DNSName") or "").rstrip(".")
backend_state = self.get("BackendState") or "unknown"
online = self.get("Online")
hostname = self.get("HostName") or ""

print(f"backend_state={backend_state}")
print(f"online={online}")
print(f"hostname={hostname}")
print(f"dns_name={dns_name}")
print(f"tailscale_ips={tailscale_ips}")

if dns_name:
    print(f"recommended_magicdns=http://{dns_name}/status")
if tailscale_ips:
    first_ip = tailscale_ips.split(",")[0]
    print(f"recommended_ip=http://{first_ip}/status")
PY
