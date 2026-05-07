#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – pull-models.sh
# Lädt alle erforderlichen Ollama-Modelle herunter
# =============================================================================
set -euo pipefail

OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OLLAMA_URL="http://localhost:$OLLAMA_PORT"
OLLAMA_CMD=(ollama)

if ! command -v ollama >/dev/null 2>&1; then
  if command -v docker >/dev/null 2>&1 && docker compose ps --services --status running 2>/dev/null | grep -qx 'ollama'; then
    OLLAMA_CMD=(docker compose exec -T ollama ollama)
  else
    echo "❌ Ollama CLI nicht gefunden und kein laufender Ollama-Container erkannt"
    exit 1
  fi
fi

# Prüfen ob Ollama erreichbar ist
if ! curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
  echo "❌ Ollama ist nicht erreichbar auf $OLLAMA_URL"
  echo "   Starte zuerst: make up"
  exit 1
fi

echo "→ Ollama verfügbar auf $OLLAMA_URL"
echo ""

pull_model() {
  local model="$1"
  local priority="$2"
  echo "  → Lade $model (Priorität: $priority)..."
  if "${OLLAMA_CMD[@]}" pull "$model"; then
    echo "  ✅ $model heruntergeladen"
  else
    echo "  ❌ Fehler beim Herunterladen von $model"
  fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Kirobi Modell-Download"
echo "  Gesamtgröße: ~20-30 GB für Basis-Modelle"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "→ Phase 1: Basis-Modelle (essentiell, ~10 GB)"
pull_model "llama3.1:8b" "KRITISCH"
pull_model "nomic-embed-text" "KRITISCH"
pull_model "mistral:7b" "KRITISCH"

echo ""
echo "→ Phase 2: Erweiterte Modelle (~25 GB zusätzlich)"
confirm=""
if [ -t 0 ]; then
  read -p "Jetzt Phase 2 Modelle herunterladen? [j/N] " confirm
fi
if [ "${confirm,,}" = "j" ]; then
  pull_model "phi3.5:3.8b" "HOCH"
  pull_model "qwen2.5-coder:7b" "HOCH"
  pull_model "llama3.1:70b" "HOCH"
fi

echo ""
echo "→ Phase 3: Spezialmodelle (optional)"
confirm=""
if [ -t 0 ]; then
  read -p "Jetzt Phase 3 Modelle herunterladen? [j/N] " confirm
fi
if [ "${confirm,,}" = "j" ]; then
  pull_model "deepseek-r1:32b" "OPTIONAL"
  pull_model "qwen2.5-coder:32b" "OPTIONAL"
  pull_model "llava:13b" "OPTIONAL"
  pull_model "bge-m3" "OPTIONAL"
fi

echo ""
echo "✅ Modell-Download abgeschlossen!"
echo "→ Verfügbare Modelle:"
"${OLLAMA_CMD[@]}" list
