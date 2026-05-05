#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – init-folders.sh
# Erstellt alle erforderlichen Verzeichnisse und setzt Berechtigungen
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "→ Initialisiere Verzeichnisse in: $REPO_ROOT"

# Funktion: Verzeichnis erstellen wenn nicht vorhanden
ensure_dir() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    echo "  ✓ Erstellt: $dir"
  else
    echo "  ℹ Vorhanden: $dir"
  fi
}

# Daten-Verzeichnisse (außerhalb des Repos, auf dem Host-System)
DATA_BASE="${KIROBI_DATA_PATH:-/var/kirobi/data}"

echo ""
echo "→ Erstelle Daten-Verzeichnisse unter $DATA_BASE"

ensure_dir "$DATA_BASE/ollama"
ensure_dir "$DATA_BASE/qdrant"
ensure_dir "$DATA_BASE/postgres"
ensure_dir "$DATA_BASE/openwebui"
ensure_dir "$DATA_BASE/flowise"
ensure_dir "$DATA_BASE/backups/qdrant"
ensure_dir "$DATA_BASE/backups/postgres"
ensure_dir "$DATA_BASE/backups/canon"
ensure_dir "$DATA_BASE/backups/experiences"
ensure_dir "$DATA_BASE/logs"

# Berechtigungen setzen
chmod 700 "$DATA_BASE" 2>/dev/null || echo "  ⚠ Konnte Berechtigungen nicht setzen"

echo ""
echo "→ Prüfe Repository-Struktur"

# Wichtige Repo-Verzeichnisse sicherstellen
for dir in \
  "sources/inbox" "sources/imports" "sources/chats" "sources/docs" \
  "sources/apis" "sources/web-research" "sources/media" "sources/audio" \
  "sources/video" "sources/images" "sources/spreadsheets" "sources/models-3d" \
  "extracts/public" "extracts/workspace" "extracts/family-private" \
  "extracts/research" "extracts/business" "extracts/technical" \
  "extracts/media" "extracts/audio" "extracts/visual" "extracts/structured" \
  "clusters/public" "clusters/workspace" "clusters/family-private" \
  "clusters/themes" "clusters/projects" "clusters/models" \
  "clusters/patterns" "clusters/conflicts" "clusters/opportunities" "clusters/strategy" \
  "quarantine/failed-ingests" "quarantine/redacted" \
  "quarantine/uncertain" "quarantine/review-needed" \
  "analytics/dashboards" \
  "archive/superseded" "archive/exports" "archive/snapshots" "archive/retired-ideas"
do
  ensure_dir "$REPO_ROOT/$dir"
done

# .gitkeep für leere Verzeichnisse
echo ""
echo "→ Erstelle .gitkeep-Dateien für leere Verzeichnisse"

for dir in \
  "sources/inbox" "sources/imports" "extracts/public" "extracts/workspace" \
  "extracts/family-private" "clusters/public" "clusters/workspace" \
  "quarantine/failed-ingests" "quarantine/redacted" \
  "archive/superseded" "archive/exports" "archive/snapshots"
do
  GITKEEP="$REPO_ROOT/$dir/.gitkeep"
  if [ ! -f "$GITKEEP" ]; then
    touch "$GITKEEP"
    echo "  ✓ .gitkeep: $dir"
  fi
done

echo ""
echo "✅ Verzeichnis-Initialisierung abgeschlossen!"
echo "→ Führe 'make up' aus um die Services zu starten."
