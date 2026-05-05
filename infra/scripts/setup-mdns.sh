#!/usr/bin/env bash
# =============================================================================
# Kirobi mDNS Setup — make `kirobi.local` resolvable on the LAN
# =============================================================================
# Publishes an Avahi alias so any device on the same network can reach
# the Caddy reverse proxy (port 80/443) at http(s)://kirobi.local.
#
# Idempotent: safe to run repeatedly. Requires sudo.
# =============================================================================
set -euo pipefail

HOSTNAME_ALIAS="${KIROBI_HOSTNAME:-kirobi.local}"
ALIAS_NAME="${HOSTNAME_ALIAS%.local}"
SERVICE_FILE="/etc/avahi/services/kirobi.service"

echo "→ Kirobi mDNS Setup ($HOSTNAME_ALIAS)"

if ! command -v avahi-daemon >/dev/null 2>&1; then
  echo "  ⚠ avahi-daemon not installed."
  if command -v apt-get >/dev/null 2>&1; then
    echo "  → Installing avahi-daemon and avahi-utils via apt-get…"
    sudo apt-get update -qq
    sudo apt-get install -y avahi-daemon avahi-utils
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y avahi avahi-tools
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm avahi
  else
    echo "  ✗ Unknown package manager. Install avahi-daemon manually."
    exit 1
  fi
fi

echo "  → Enabling avahi-daemon…"
sudo systemctl enable --now avahi-daemon

# Make the host advertise the requested hostname.
CURRENT_HOSTNAME="$(hostname)"
if [ "$CURRENT_HOSTNAME" != "$ALIAS_NAME" ]; then
  echo "  → Adding mDNS alias $HOSTNAME_ALIAS via /etc/avahi/services/kirobi.service"
  sudo mkdir -p /etc/avahi/services
  sudo tee "$SERVICE_FILE" >/dev/null <<EOF
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Kirobi (%h)</name>
  <service>
    <type>_http._tcp</type>
    <port>80</port>
    <txt-record>path=/</txt-record>
  </service>
  <service>
    <type>_https._tcp</type>
    <port>443</port>
  </service>
</service-group>
EOF
  sudo systemctl reload avahi-daemon || sudo systemctl restart avahi-daemon
  echo "  ✓ Avahi service published"
fi

# Probe the result.
echo ""
echo "→ Probe:"
if command -v avahi-resolve >/dev/null 2>&1; then
  if avahi-resolve -n "$HOSTNAME_ALIAS" 2>/dev/null; then
    echo "  ✓ $HOSTNAME_ALIAS resolved"
  else
    echo "  ⚠ $HOSTNAME_ALIAS not yet visible — may take a few seconds"
  fi
else
  getent hosts "$HOSTNAME_ALIAS" || echo "  ⚠ getent could not resolve $HOSTNAME_ALIAS"
fi

LAN_IP=""
if command -v hostname >/dev/null 2>&1 && hostname -I >/dev/null 2>&1; then
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
fi
if [ -z "$LAN_IP" ] && command -v ip >/dev/null 2>&1; then
  LAN_IP="$(ip -o -4 addr show scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -n1)"
fi
echo ""
echo "Kirobi sollte jetzt erreichbar sein unter:"
echo "  • http://$HOSTNAME_ALIAS/"
echo "  • https://$HOSTNAME_ALIAS/         (TLS via Caddy internal CA)"
[ -n "${LAN_IP:-}" ] && echo "  • http://$LAN_IP/                  (LAN-IP)"
echo ""
echo "Tipp: iOS / macOS finden mDNS-Hosts out-of-the-box. Auf Windows hilft"
echo "      die Installation von Bonjour Print Services oder iTunes."
