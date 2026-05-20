#!/usr/bin/env bash
# verify-apk.sh — Kirobi APK Integrity Checker
# Prüft heruntergeladene APK-Dateien gegen bekannte SHA256-Checksums
#
# Usage:
#   ./verify-apk.sh <apk-file>
#   ./verify-apk.sh Kirobi-v11-debug.apk
#   ./verify-apk.sh --list              # Alle bekannten APKs anzeigen
#   ./verify-apk.sh --update            # Checksums aus lokalem APK-Verzeichnis neu scannen
#   ./verify-apk.sh --generate <apk>    # Checksum für neue APK ausgeben (kein Vergleich)
#
# Exit Codes:
#   0 = APK verifiziert ✅
#   1 = Checksum-Fehler ❌ (Datei manipuliert oder korrupt)
#   2 = Unbekannte APK (nicht in Checksums-DB)
#   3 = Datei nicht gefunden
#   4 = sha256sum / shasum nicht verfügbar

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APK_DIR="${APK_DIR:-$(dirname "$SCRIPT_DIR")}"   # Standard: parent des scripts-Ordners
CHECKSUMS_DB="${CHECKSUMS_DB:-${SCRIPT_DIR}/apk-checksums.db}"
GITHUB_REPO="Kirobi92/OpenDisruption"
GITHUB_RELEASE_URL="https://github.com/${GITHUB_REPO}/releases"

# ─── Farben ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Checksums-DB laden (falls vorhanden) ─────────────────────────────────────
declare -A KNOWN_CHECKSUMS=()
declare -A APK_TAGS=()

_load_checksums_db() {
  if [[ -f "$CHECKSUMS_DB" ]]; then
    while IFS='|' read -r name hash tag; do
      [[ "$name" =~ ^# ]] && continue
      [[ -z "$name" ]] && continue
      KNOWN_CHECKSUMS["$name"]="$hash"
      APK_TAGS["$name"]="${tag:-unknown}"
    done < "$CHECKSUMS_DB"
  fi
}

# ─── Fallback: hartcodierte Checksums (Stand: 2026-05-20) ────────────────────
_load_hardcoded_checksums() {
  # v4–v9 historisch
  KNOWN_CHECKSUMS["Kirobi-v4-debug.apk"]="27682aaac9425556cd7153bf072613e6c5769a5e193687a9765074bf6507f709"
  KNOWN_CHECKSUMS["Kirobi-v5-debug.apk"]="66473e90b23df4ec43359db0dcef69da151b7aa3f251fd7a7253eb9bacdf68f0"
  KNOWN_CHECKSUMS["Kirobi-v6-debug.apk"]="a85232975ec9c3c3f217ac10da4882672b859c6984a78fad66acaab683e6f932"
  KNOWN_CHECKSUMS["Kirobi-v7-debug.apk"]="d7ffb6c5d6c67c0caf1e30a48f4e06e7a88411000d0392ba11c2b34d8766a3cd"
  KNOWN_CHECKSUMS["Kirobi-v8-debug.apk"]="07e091083331d7723084cb013eb7dc51dd6fb5b0a77767aa822e71de553de8ba"
  KNOWN_CHECKSUMS["Kirobi-v9-debug.apk"]="3393f3e4bdf80ace0652d79d4becd080153b93ea299a95fa8cd86cb4137d7fdb"
  APK_TAGS["Kirobi-v4-debug.apk"]="v4.0.0"
  APK_TAGS["Kirobi-v5-debug.apk"]="v5.0.0"
  APK_TAGS["Kirobi-v6-debug.apk"]="v6.0.0"
  APK_TAGS["Kirobi-v7-debug.apk"]="v7.0.0"
  APK_TAGS["Kirobi-v8-debug.apk"]="v8.0.0"
  APK_TAGS["Kirobi-v9-debug.apk"]="v9.0.0"
  # v10 — Stable Release
  KNOWN_CHECKSUMS["Kirobi-v10-debug.apk"]="04541c00f7f2ba2d1a375bb664fa715aaaa2779c1302b2f5f03197b58fce88a4"
  KNOWN_CHECKSUMS["Kirobi-v10-release.apk"]="30191632eacad466d1f66078447a1ced216f1e9d9f6a21c5feb350ab988a7730"
  KNOWN_CHECKSUMS["Kirobi-v10-release-signed.apk"]="18a1bcb3ea524ecc53700c3dd3052e54272371e1be1d5c4cbd79eb04682f7eb2"
  KNOWN_CHECKSUMS["Kirobi-v10.2-milestone-fired-debug.apk"]="65befc5b6e6aedbb3a0cb1ed826d926e3e83efcfe93a8abab4d4dead9386d347"
  KNOWN_CHECKSUMS["Kirobi-v10.3-download-history-debug.apk"]="12b2500731bc654bde2cabe19628eaa74f91868c4c5f7be3f4b7b55af85ddc18"
  KNOWN_CHECKSUMS["Kirobi-v10.4-week-nav-debug.apk"]="0afc27a3fe5ed7f1f4dee64d2e84a33d9ad1d4c27d2c14dd2a59c3101a4f3266"
  KNOWN_CHECKSUMS["Kirobi-v10.5-chat-agent-connect-debug.apk"]="a26ca36a29721548a064def6389e771e0d63b5a87654797565e37d0b64cad060"
  KNOWN_CHECKSUMS["Kirobi-v10.5-keyboard-nav-debug.apk"]="170ba5dd00f263f090210bfc6c0ba07d4879de27034757409c34277b0631caa7"
  KNOWN_CHECKSUMS["Kirobi-v10.6-tab-focus-debug.apk"]="cc462790316e7eab9fae698bfda8925819219014695f0cff33550fd93e3dc145"
  KNOWN_CHECKSUMS["Kirobi-v10.7-accessibility-debug.apk"]="cc462790316e7eab9fae698bfda8925819219014695f0cff33550fd93e3dc145"
  KNOWN_CHECKSUMS["Kirobi-v10.8-swipe-touch-debug.apk"]="cc462790316e7eab9fae698bfda8925819219014695f0cff33550fd93e3dc145"
  APK_TAGS["Kirobi-v10-debug.apk"]="v10.0.0"
  APK_TAGS["Kirobi-v10-release.apk"]="v10.0.0"
  APK_TAGS["Kirobi-v10-release-signed.apk"]="v10.0.0"
  APK_TAGS["Kirobi-v10.2-milestone-fired-debug.apk"]="v10.2.0"
  APK_TAGS["Kirobi-v10.3-download-history-debug.apk"]="v10.3.0"
  APK_TAGS["Kirobi-v10.4-week-nav-debug.apk"]="v10.4.0"
  APK_TAGS["Kirobi-v10.5-chat-agent-connect-debug.apk"]="v10.5.0"
  APK_TAGS["Kirobi-v10.5-keyboard-nav-debug.apk"]="v10.5.0"
  APK_TAGS["Kirobi-v10.6-tab-focus-debug.apk"]="v10.6.0"
  APK_TAGS["Kirobi-v10.7-accessibility-debug.apk"]="v10.7.0"
  APK_TAGS["Kirobi-v10.8-swipe-touch-debug.apk"]="v10.8.0"
  # v11 — Aktuell in Entwicklung
  KNOWN_CHECKSUMS["Kirobi-v11-debug.apk"]="5ddcf57f42c3fc0af03f04dc4bf7cafd31b0ed00c8ece4ccf9f4368154f02848"
  APK_TAGS["Kirobi-v11-debug.apk"]="v11.0.0-beta"
  # HINWEIS: v11-release und weitere Versionen werden automatisch via
  # update-apk-checksums.sh (cron) in apk-checksums.db aufgenommen.
  # Nach jedem Gradle-Build: scripts/update-apk-checksums.sh --notify
}

# DB laden, dann hardcoded als Fallback für fehlende Einträge
_load_checksums_db
_load_hardcoded_checksums

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────
_sha256() {
  local file="$1"
  if command -v sha256sum &>/dev/null; then
    sha256sum "$file" | awk '{print $1}'
  elif command -v shasum &>/dev/null; then
    shasum -a 256 "$file" | awk '{print $1}'
  else
    echo -e "${RED}❌ Fehler: sha256sum oder shasum nicht gefunden.${NC}" >&2
    exit 4
  fi
}

_list_known() {
  echo -e "${CYAN}${BOLD}Bekannte Kirobi APKs:${NC}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  printf "%-40s  %-12s  %s\n" "APK" "Release" "SHA256 (erste 16 Zeichen)"
  echo "───────────────────────────────────────────────────────────────────────"
  for apk in "${!KNOWN_CHECKSUMS[@]}"; do
    local hash="${KNOWN_CHECKSUMS[$apk]}"
    local tag="${APK_TAGS[$apk]:-?}"
    printf "%-40s  %-12s  %s...\n" "$apk" "$tag" "${hash:0:16}"
  done
  echo ""
  echo -e "Download: ${CYAN}${GITHUB_RELEASE_URL}${NC}"
}

# ─── Argumente verarbeiten ────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo -e "${CYAN}${BOLD}Kirobi APK Verify Script${NC}"
  echo ""
  echo "Usage: $0 <apk-file>"
  echo "       $0 --list"
  echo "       $0 --generate <apk-file>"
  echo ""
  _list_known
  exit 0
fi

case "$1" in
  --list|-l)
    _list_known
    exit 0
    ;;
  --update|-u)
    echo -e "${CYAN}${BOLD}🔄 Checksums aus lokalem APK-Verzeichnis aktualisieren...${NC}"
    echo "Scan: $APK_DIR"
    echo ""
    {
      echo "# Kirobi APK Checksums DB — automatisch generiert $(date '+%Y-%m-%d %H:%M')"
      echo "# Format: name|sha256|tag"
      for apk_path in "$APK_DIR"/*.apk; do
        [[ -f "$apk_path" ]] || continue
        apk_name=$(basename "$apk_path")
        hash=$(_sha256 "$apk_path")
        # Tag aus Dateiname ableiten
        tag="unknown"
        if [[ "$apk_name" =~ Kirobi-(v[0-9]+\.[0-9]+(\.[0-9]+)?(-[a-z]+)?) ]]; then
          ver="${BASH_REMATCH[1]}"
          if [[ "$apk_name" == *"release-signed"* ]]; then
            tag="${ver}"
          elif [[ "$apk_name" == *"release"* ]]; then
            tag="${ver}"
          else
            tag="${ver}-beta"
          fi
        fi
        echo "${apk_name}|${hash}|${tag}"
        echo -e "  ${GREEN}✓${NC} $apk_name" >&2
      done
    } > "$CHECKSUMS_DB"
    echo ""
    echo -e "${GREEN}✅ DB aktualisiert: ${CHECKSUMS_DB}${NC}"
    ENTRIES=$(grep -c '^[^#]' "$CHECKSUMS_DB" 2>/dev/null || echo 0)
    echo "   $ENTRIES APKs gespeichert"
    exit 0
    ;;
  --generate|-g)
    if [[ $# -lt 2 ]]; then
      echo -e "${RED}Fehler: Bitte APK-Datei angeben.${NC}"
      exit 1
    fi
    APK_GEN="$2"
    if [[ ! -f "$APK_GEN" ]]; then
      echo -e "${RED}❌ Datei nicht gefunden: $APK_GEN${NC}"
      exit 3
    fi
    HASH=$(_sha256 "$APK_GEN")
    echo -e "${CYAN}SHA256 für ${BOLD}$APK_GEN${NC}${CYAN}:${NC}"
    echo "  $HASH"
    echo ""
    echo "In KNOWN_CHECKSUMS eintragen:"
    echo "  [\"$(basename "$APK_GEN")\"]=\"$HASH\""
    exit 0
    ;;
esac

# ─── Hauptprüfung ─────────────────────────────────────────────────────────────
APK_FILE="$1"
APK_BASENAME="$(basename "$APK_FILE")"

if [[ ! -f "$APK_FILE" ]]; then
  echo -e "${RED}❌ Fehler: Datei nicht gefunden: $APK_FILE${NC}"
  exit 3
fi

echo -e "${CYAN}${BOLD}🔍 Kirobi APK Integrity Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Datei:    $APK_FILE"
FILESIZE=$(stat -c%s "$APK_FILE" 2>/dev/null || stat -f%z "$APK_FILE" 2>/dev/null || echo "?")
echo "Größe:    $(du -h "$APK_FILE" | cut -f1) (${FILESIZE} Bytes)"
if [[ -n "${APK_TAGS[$APK_BASENAME]:-}" ]]; then
  echo "Release:  ${APK_TAGS[$APK_BASENAME]}"
fi
echo ""

echo -n "SHA256 berechnen... "
ACTUAL_HASH=$(_sha256 "$APK_FILE")
echo "fertig"
echo ""
echo "Berechneter Hash:"
echo "  $ACTUAL_HASH"
echo ""

# ─── Bekannte APK? ────────────────────────────────────────────────────────────
if [[ -z "${KNOWN_CHECKSUMS[$APK_BASENAME]:-}" ]]; then
  echo -e "${YELLOW}⚠️  Unbekannte APK: '$APK_BASENAME'${NC}"
  echo "Diese Datei ist nicht in der Checksums-Datenbank."
  echo ""
  echo "Tipp: Neue APK aufnehmen mit:"
  echo "  $0 --generate \"$APK_FILE\""
  echo ""
  _list_known
  exit 2
fi

EXPECTED_HASH="${KNOWN_CHECKSUMS[$APK_BASENAME]}"
echo "Erwarteter Hash (${APK_TAGS[$APK_BASENAME]:-GitHub Release}):"
echo "  $EXPECTED_HASH"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "$ACTUAL_HASH" == "$EXPECTED_HASH" ]]; then
  echo -e "${GREEN}${BOLD}✅ VERIFIZIERT — APK ist authentisch und unverändert${NC}"
  echo ""
  echo "Du kannst die APK sicher installieren:"
  echo "  adb install \"$APK_FILE\""
  echo "  oder: Datei auf Android-Gerät übertragen und öffnen"
  exit 0
else
  echo -e "${RED}${BOLD}❌ FEHLER — Checksum stimmt NICHT überein!${NC}"
  echo ""
  echo -e "${RED}Die Datei könnte:${NC}"
  echo "  • Beim Download beschädigt worden sein"
  echo "  • Manipuliert / verändert worden sein"
  echo "  • Eine andere Version sein"
  echo ""
  echo "Empfehlung: Erneut von GitHub herunterladen:"
  echo "  ${GITHUB_RELEASE_URL}/tag/${APK_TAGS[$APK_BASENAME]:-latest}"
  exit 1
fi
