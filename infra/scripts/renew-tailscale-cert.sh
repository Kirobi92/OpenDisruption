#!/usr/bin/env bash
# Renew the Let's Encrypt cert that Tailscale issues for this node and
# reload Caddy so the new cert is picked up. Run from cron weekly.
#
# `tailscale cert` only re-fetches when the existing cert is within the
# renewal window, so it's safe to run often.
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CERT_DIR="${REPO_ROOT}/infra/caddy/certs"
HOSTNAME="${KIROBI_TAILSCALE_HOSTNAME:-pop-os.taildd322d.ts.net}"

mkdir -p "${CERT_DIR}"
cd "${CERT_DIR}"

tailscale cert \
  --cert-file "${HOSTNAME}.crt" \
  --key-file  "${HOSTNAME}.key" \
  "${HOSTNAME}"

# Hot-reload Caddy without dropping connections.
docker exec kirobi-caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || \
  docker compose -f "${REPO_ROOT}/docker-compose.yml" restart caddy
