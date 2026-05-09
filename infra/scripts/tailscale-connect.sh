#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

apply=false
for arg in "$@"; do
  case "$arg" in
    --apply)
      apply=true
      ;;
    --help|-h)
      cat <<'EOF'
Usage: bash infra/scripts/tailscale-connect.sh [--apply]

Liests Tailscale-Parameter aus der lokalen .env und zeigt standardmaessig nur den
sicheren tailscale-up Aufruf. Mit --apply wird der Aufruf wirklich ausgefuehrt.

Erwartete .env-Werte:
  TAILSCALE_AUTH_KEY=...
  TAILSCALE_HOSTNAME=...
  TAILSCALE_SSH=true
  TAILSCALE_ACCEPT_DNS=false
  TAILSCALE_ADVERTISE_TAGS=tag:kirobi
EOF
      exit 0
      ;;
    *)
      echo "Unbekanntes Argument: $arg" >&2
      exit 1
      ;;
  esac
done

if [ -f .env ]; then
  while IFS=$'\t' read -r key value; do
    case "$key" in
      TAILSCALE_AUTH_KEY)
        if [ -z "${TAILSCALE_AUTH_KEY:-}" ]; then
          TAILSCALE_AUTH_KEY="$value"
        fi
        ;;
      TAILSCALE_HOSTNAME)
        if [ -z "${TAILSCALE_HOSTNAME:-}" ]; then
          TAILSCALE_HOSTNAME="$value"
        fi
        ;;
      TAILSCALE_SSH)
        if [ -z "${TAILSCALE_SSH:-}" ]; then
          TAILSCALE_SSH="$value"
        fi
        ;;
      TAILSCALE_ACCEPT_DNS)
        if [ -z "${TAILSCALE_ACCEPT_DNS:-}" ]; then
          TAILSCALE_ACCEPT_DNS="$value"
        fi
        ;;
      TAILSCALE_ADVERTISE_TAGS)
        if [ -z "${TAILSCALE_ADVERTISE_TAGS:-}" ]; then
          TAILSCALE_ADVERTISE_TAGS="$value"
        fi
        ;;
    esac
  done < <(
    python3 - <<'PY'
from pathlib import Path
import re

keys = {
    "TAILSCALE_AUTH_KEY",
    "TAILSCALE_HOSTNAME",
    "TAILSCALE_SSH",
    "TAILSCALE_ACCEPT_DNS",
    "TAILSCALE_ADVERTISE_TAGS",
}

for raw_line in Path(".env").read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue

    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
    if not match:
        continue

    key, value = match.groups()
    if key not in keys:
        continue

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]

    print(f"{key}\t{value}")
PY
  )
fi

auth_key="${TAILSCALE_AUTH_KEY:-}"
hostname="${TAILSCALE_HOSTNAME:-}"
ssh_enabled="${TAILSCALE_SSH:-true}"
accept_dns="${TAILSCALE_ACCEPT_DNS:-false}"
advertise_tags="${TAILSCALE_ADVERTISE_TAGS:-}"

if [ -z "$auth_key" ]; then
  echo "TAILSCALE_AUTH_KEY fehlt in .env." >&2
  exit 1
fi

if ! command -v tailscale >/dev/null 2>&1; then
  echo "tailscale CLI ist auf diesem Host nicht installiert." >&2
  exit 1
fi

cmd=(
  tailscale up
  --auth-key="$auth_key"
  --accept-dns="$accept_dns"
  --reset
)

if [ "$ssh_enabled" = "true" ] || [ "$ssh_enabled" = "1" ] || [ "$ssh_enabled" = "yes" ]; then
  cmd+=(--ssh)
fi

if [ -n "$hostname" ]; then
  cmd+=(--hostname="$hostname")
fi

if [ -n "$advertise_tags" ]; then
  cmd+=(--advertise-tags="$advertise_tags")
fi

if ! $apply; then
  echo "tailscale_connect=dry_run"
  echo "hostname=${hostname:-auto}"
  echo "ssh_enabled=$ssh_enabled"
  echo "accept_dns=$accept_dns"
  if [ -n "$advertise_tags" ]; then
    echo "advertise_tags=$advertise_tags"
  fi
  echo "next_step=sudo --preserve-env=TAILSCALE_AUTH_KEY,TAILSCALE_HOSTNAME,TAILSCALE_SSH,TAILSCALE_ACCEPT_DNS,TAILSCALE_ADVERTISE_TAGS bash infra/scripts/tailscale-connect.sh --apply"
  exit 0
fi

sudo --preserve-env=TAILSCALE_AUTH_KEY,TAILSCALE_HOSTNAME,TAILSCALE_SSH,TAILSCALE_ACCEPT_DNS,TAILSCALE_ADVERTISE_TAGS "${cmd[@]}"
