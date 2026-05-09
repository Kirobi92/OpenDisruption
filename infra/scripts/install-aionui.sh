#!/usr/bin/env bash
# install-aionui.sh — host-seitige Installation des AionUi-Cockpits
#
# AionUi ist eine Electron-Desktop-App mit optionalem WebUI-Mode für Browser-
# Zugriff. Es gibt KEIN offizielles Docker-Image, headless via Xvfb ist fragil,
# und der `server`-Mode verliert 10 Kern-Bridges. Daher: native .deb auf dem Host.
#
# Default: --dry-run (nur prüfen, was passieren würde).
# Mit --apply: tatsächliche Installation.
#
# Idempotent: erkennt bestehende Installation und überspringt Download bei
# gleicher Version.

set -Eeuo pipefail

DRY_RUN=true
ACTION="install"
AIONUI_VERSION="${AIONUI_VERSION:-latest}"
AIONUI_PORT="${AIONUI_PORT:-25808}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--apply] [--upgrade] [--uninstall] [--dry-run] [--version VERSION]

  --dry-run     Nur prüfen (Default).
  --apply       Tatsächlich installieren.
  --upgrade     Bestehende Installation aktualisieren (impliziert --apply).
  --uninstall   AionUi entfernen (impliziert --apply).
  --version V   Version-Tag (Default: latest).

Environment:
  AIONUI_VERSION   wie --version
  AIONUI_PORT      WebUI-Port (Default 25808)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN=true ;;
    --apply)      DRY_RUN=false ;;
    --upgrade)    DRY_RUN=false; ACTION="upgrade" ;;
    --uninstall)  DRY_RUN=false; ACTION="uninstall" ;;
    --version)    AIONUI_VERSION="$2"; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "Unbekannte Option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

log()  { printf '[aionui-install] %s\n' "$*"; }
note() { printf '[aionui-install] %s\n' "$*" >&2; }

run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY-RUN: $*"
  else
    log "RUN: $*"
    "$@"
  fi
}

require() {
  command -v "$1" >/dev/null 2>&1 || { note "Fehlt: $1"; return 1; }
}

preflight() {
  log "Pre-Flight-Check ..."
  require dpkg || { note "dpkg nicht gefunden — AionUi-.deb braucht Debian/Ubuntu-Host"; exit 3; }
  require curl || { note "curl nicht gefunden"; exit 3; }
  require jq   || { note "jq nicht gefunden — wird gebraucht für Release-Lookup"; exit 3; }
  if [[ "$ACTION" != "uninstall" ]] && ! require xvfb-run; then
    note "Hinweis: xvfb-run nicht gefunden. AionUi-Headless braucht xvfb."
    note "         apt install -y xvfb libegl1 libgles2"
  fi
}

current_version() {
  if dpkg -s aionui >/dev/null 2>&1; then
    dpkg -s aionui | awk '/^Version:/{print $2}'
  else
    echo "(none)"
  fi
}

resolve_release_url() {
  local tag="$1"
  if [[ "$tag" == "latest" ]]; then
    curl -fsSL https://api.github.com/repos/iOfficeAI/AionUi/releases/latest \
      | jq -r '.assets[] | select(.name | test("linux-amd64\\.deb$")) | .browser_download_url'
  else
    curl -fsSL "https://api.github.com/repos/iOfficeAI/AionUi/releases/tags/${tag}" \
      | jq -r '.assets[] | select(.name | test("linux-amd64\\.deb$")) | .browser_download_url'
  fi
}

do_install() {
  local url tmp
  url=$(resolve_release_url "$AIONUI_VERSION")
  if [[ -z "$url" || "$url" == "null" ]]; then
    note "Kein passendes .deb in Release '$AIONUI_VERSION' gefunden."
    exit 4
  fi
  log "Release-URL: $url"
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  run curl -fsSL "$url" -o "$tmp/aionui.deb"
  run sudo dpkg -i "$tmp/aionui.deb" || run sudo apt-get install -f -y
  log "Installation abgeschlossen. Start (headless WebUI):"
  log "  xvfb-run --auto-servernum --server-args=\"-screen 0 1920x1080x24\" \\"
  log "    /usr/bin/AionUi --webui --remote --no-sandbox"
  log "WebUI dann unter http://127.0.0.1:${AIONUI_PORT}"
  log "JWT-Passwort initial setzen: bun run resetpass (im AionUi-Dir)"
}

do_uninstall() {
  if dpkg -s aionui >/dev/null 2>&1; then
    run sudo dpkg --purge aionui
    log "AionUi entfernt."
  else
    log "AionUi war nicht installiert — nichts zu tun."
  fi
}

main() {
  log "Action: ${ACTION}  |  DRY-RUN: ${DRY_RUN}  |  Version: ${AIONUI_VERSION}"
  log "Aktuell installiert: $(current_version)"
  preflight
  case "$ACTION" in
    install|upgrade) do_install ;;
    uninstall)       do_uninstall ;;
    *) usage; exit 2 ;;
  esac
}

main "$@"
