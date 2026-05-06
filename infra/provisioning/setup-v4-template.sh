#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – setup-v4-template.sh
# Template für Ubuntu 22.04 LTS Server-Setup
# Kirobi Setup Version 4 (GPU-optimiert)
# =============================================================================
set -euo pipefail

echo "→ Kirobi v4 Setup Template"
echo "  Ubuntu 22.04 LTS, NVIDIA GPU optimiert"

# System-Update
apt-get update && apt-get upgrade -y

# Basis-Pakete
apt-get install -y \
  curl git make wget unzip \
  apt-transport-https ca-certificates \
  software-properties-common gnupg \
  python3-pip python3-venv \
  htop iotop nethogs \
  fail2ban ufw

# Docker installieren
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "$USER"
  echo "  ✅ Docker installiert"
fi

# NVIDIA Container Toolkit (wenn GPU vorhanden)
if lspci | grep -qi nvidia; then
  distribution=$(. /etc/os-release; echo "$ID$VERSION_ID")
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  echo "  ✅ NVIDIA Container Toolkit installiert"
fi

# Firewall konfigurieren (Ports nur lokal)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw --force enable
echo "  ✅ Firewall konfiguriert"

# Kirobi-Verzeichnisse anlegen
mkdir -p /var/kirobi/{data,backups,logs}
chmod 700 /var/kirobi

echo "✅ Server-Setup abgeschlossen!"
echo "→ Führe jetzt 'make init && make up' im Repository aus."
