#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – bootstrap.sh
# Vollständiges Bootstrap-Skript für die erste Einrichtung
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║     Kirobi / Disruptive OS – Bootstrap        ║"
echo "║     Version 0.1.0                             ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""

# Mode-Check
MODE="${1:-full}"

case "$MODE" in
  full)
    echo "→ Vollständiger Bootstrap-Modus"
    ;;
  backup)
    echo "→ Backup-Modus"
    ;;
  check)
    echo "→ Prüf-Modus (keine Änderungen)"
    ;;
  *)
    echo "❌ Unbekannter Modus: $MODE"
    echo "   Verwendung: $0 [full|backup|check]"
    exit 1
    ;;
esac

# Voraussetzungen prüfen
check_prerequisites() {
  echo ""
  echo "→ Prüfe Voraussetzungen..."
  
  local missing=0
  
  for cmd in docker curl git make; do
    if command -v "$cmd" &>/dev/null; then
      echo "  ✅ $cmd verfügbar"
    else
      echo "  ❌ $cmd fehlt!"
      missing=$((missing + 1))
    fi
  done
  
  if ! docker compose version &>/dev/null; then
    echo "  ❌ Docker Compose v2 fehlt!"
    missing=$((missing + 1))
  else
    echo "  ✅ Docker Compose v2 verfügbar"
  fi
  
  if [ "$missing" -gt 0 ]; then
    echo "  ❌ $missing Voraussetzung(en) fehlen. Bitte installieren und erneut versuchen."
    exit 1
  fi
}

# .env prüfen/erstellen
setup_env() {
  echo ""
  echo "→ Konfiguriere Umgebungsvariablen..."
  
  if [ ! -f "$REPO_ROOT/.env" ]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
    echo "  ✅ .env aus .env.example erstellt"
    echo "  ⚠️ WICHTIG: Passe $REPO_ROOT/.env an (Passwörter ändern!)"
  else
    echo "  ℹ .env existiert bereits"
  fi
}

# Backup-Funktion
run_backup() {
  echo ""
  echo "→ Erstelle Backup..."

  # Honour env vars from .env (BACKUP_TARGET_DIR / BACKUP_RETENTION_DAYS) and
  # fall back to KIROBI_BACKUP_PATH for backwards compatibility.
  local backup_dir="${BACKUP_TARGET_DIR:-${KIROBI_BACKUP_PATH:-$REPO_ROOT/archive/snapshots}}"
  local retention_days="${BACKUP_RETENTION_DAYS:-30}"
  local timestamp
  timestamp=$(date +%Y%m%d_%H%M%S)
  local backup_name="kirobi_backup_$timestamp"

  mkdir -p "$backup_dir/$backup_name"

  # Canon und Experiences sichern
  if [ -d "$REPO_ROOT/canon" ]; then
    cp -r "$REPO_ROOT/canon" "$backup_dir/$backup_name/"
    echo "  ✅ canon/ gesichert"
  fi

  if [ -d "$REPO_ROOT/experiences" ]; then
    cp -r "$REPO_ROOT/experiences" "$backup_dir/$backup_name/"
    echo "  ✅ experiences/ gesichert"
  fi

  # Optional: kirobi-core (audit log + state) und metadata
  if [ -d "$REPO_ROOT/kirobi-core" ]; then
    cp -r "$REPO_ROOT/kirobi-core" "$backup_dir/$backup_name/"
    echo "  ✅ kirobi-core/ gesichert"
  fi

  echo "  ✅ Backup erstellt in: $backup_dir/$backup_name"

  # Retention: ältere Backups löschen, wenn BACKUP_RETENTION_DAYS gesetzt.
  if [ "$retention_days" -gt 0 ] 2>/dev/null; then
    echo "  → Bereinige Backups älter als ${retention_days} Tage in $backup_dir"
    find "$backup_dir" -maxdepth 1 -type d -name "kirobi_backup_*" \
      -mtime "+${retention_days}" -print -exec rm -rf {} + 2>/dev/null || true
  fi
}

if [ "$MODE" = "backup" ]; then
  run_backup
  exit 0
fi

# Vollständiger Bootstrap
check_prerequisites
setup_env

echo ""
echo "→ Initialisiere Verzeichnisse..."
bash "$SCRIPT_DIR/init-folders.sh"

echo ""
echo "→ Starte Docker-Services..."
cd "$REPO_ROOT" && docker compose pull
docker compose up -d

echo ""
echo "→ Warte auf Service-Start (30 Sekunden)..."
sleep 30

echo ""
echo "→ Führe Healthcheck durch..."
bash "$SCRIPT_DIR/healthcheck.sh" || echo "⚠️ Einige Services noch nicht bereit"

echo ""
echo "╔═══════════════════════════════════════════════╗"
echo "║     Bootstrap abgeschlossen!                  ║"
echo "║                                               ║"
echo "║  Open WebUI:  http://localhost:3000           ║"
echo "║  Flowise:     http://localhost:3001           ║"
echo "║  Qdrant:      http://localhost:6333           ║"
echo "╚═══════════════════════════════════════════════╝"
echo ""
echo "→ Nächste Schritte:"
echo "  1. make pull-models  (Basis-Modelle herunterladen)"
echo "  2. Open WebUI öffnen und konfigurieren"
echo "  3. Ersten Inhalt in sources/inbox/ ablegen"
