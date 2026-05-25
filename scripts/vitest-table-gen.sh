#!/usr/bin/env bash
# vitest-table-gen.sh — Kirobi APK Test-Datei-Tabelle Generator
# Parst `vitest run --reporter=json` Output und generiert die
# Test-Datei-Tabelle als Markdown für README.ci.md.
#
# Usage:
#   ./vitest-table-gen.sh              # Tabelle auf stdout ausgeben
#   ./vitest-table-gen.sh --update     # README.ci.md automatisch updaten
#   ./vitest-table-gen.sh --check      # Prüfen ob README.ci.md aktuell ist (Exit 1 bei Drift)
#   ./vitest-table-gen.sh --update --input-file results.json  # CI-Mode: JSON aus Datei statt vitest-Run
#
# Exit Codes:
#   0 = Tabelle generiert / README.ci.md aktuell
#   1 = README.ci.md nicht aktuell (--check) oder Fehler
#   2 = vitest fehlgeschlagen
#   3 = jq nicht verfügbar

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
README_CI="${PROJECT_DIR}/README.ci.md"
MODE="${1:---stdout}"
INPUT_FILE=""

# ─── Farben ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Argument-Parsing ─────────────────────────────────────────────────────────
# Extrahiere --input-file aus allen Argumenten (kann an beliebiger Position stehen)
for arg in "$@"; do
  if [[ "$arg" == --input-file=* ]]; then
    INPUT_FILE="${arg#--input-file=}"
  elif [[ "$arg" == --input-file ]]; then
    # Wird im nächsten Schleifendurchlauf behandelt
    :
  fi
done

# Handle --input-file <path> (zwei separate Argumente)
NEXT_IS_INPUT=false
for arg in "$@"; do
  if $NEXT_IS_INPUT; then
    INPUT_FILE="$arg"
    NEXT_IS_INPUT=false
  fi
  if [[ "$arg" == "--input-file" && "$arg" != "--input-file="* ]]; then
    NEXT_IS_INPUT=true
  fi
done

# ─── Abhängigkeiten prüfen ────────────────────────────────────────────────────
if ! command -v jq &>/dev/null; then
  echo -e "${RED}❌ Fehler: jq nicht gefunden. Bitte installieren: apt install jq${NC}" >&2
  exit 3
fi

if [[ -n "$INPUT_FILE" ]]; then
  # CI-Mode: JSON aus Datei lesen statt vitest auszuführen
  if [[ ! -f "$INPUT_FILE" ]]; then
    echo -e "${RED}❌ Fehler: Input-Datei nicht gefunden: $INPUT_FILE${NC}" >&2
    exit 2
  fi
  echo -e "${CYAN}📂 Lese vitest JSON aus Datei: $INPUT_FILE${NC}" >&2
  VITEST_JSON=$(cat "$INPUT_FILE")
else
  # Standard-Mode: vitest selbst ausführen
  if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo -e "${RED}❌ Fehler: frontend/ Verzeichnis nicht gefunden: $FRONTEND_DIR${NC}" >&2
    exit 1
  fi

  echo -e "${CYAN}🧪 Führe vitest run --reporter=json aus...${NC}" >&2

  VITEST_JSON=$(cd "$FRONTEND_DIR" && npx vitest run --reporter=json 2>/dev/null) || {
    echo -e "${RED}❌ vitest fehlgeschlagen${NC}" >&2
    exit 2
  }
fi

# ─── JSON validieren ──────────────────────────────────────────────────────────
if ! echo "$VITEST_JSON" | jq -e '.testResults' >/dev/null 2>&1; then
  echo -e "${RED}❌ vitest JSON-Output konnte nicht geparst werden${NC}" >&2
  exit 2
fi

# ─── Gesamtstatistik extrahieren ──────────────────────────────────────────────
NUM_TOTAL=$(echo "$VITEST_JSON" | jq -r '.numTotalTests')
NUM_PASSED=$(echo "$VITEST_JSON" | jq -r '.numPassedTests')
NUM_FAILED=$(echo "$VITEST_JSON" | jq -r '.numFailedTests')

echo -e "   ${GREEN}${NUM_PASSED}/${NUM_TOTAL} passed${NC}, ${RED}${NUM_FAILED} failed${NC}" >&2

# ─── Per-File Tabelle generieren ──────────────────────────────────────────────
# Extrahiere: Dateiname, Test-Anzahl, Komponenten (unique ancestorTitles[0])
# und Sub-Komponenten-Details (unique ancestorTitles[1] sofern vorhanden)

generate_table() {
  local index=1
  local table=""
  local total_tests=0

  # Header
  table+="| # | Datei | Tests | Komponenten |\n"
  table+="|---|---|---|---|\n"

  # Jede Test-Datei durchgehen, sortiert nach Dateiname
  while IFS=$'\t' read -r filename test_count titles_str; do
    local komponenten_col=""

    # titles_str = \u0001-separierte unique ancestorTitles[0] — in JSON-Array konvertieren
    local titles_json
    titles_json=$(echo "$titles_str" | jq -Rs 'split("\u0001") | map(select(length > 0))')

    # Verarbeite in bash für smarte Komponenten-Extraktion
    local base_name="${filename%.test.tsx}"

    # Extrahiere Prefix/Suffix für jeden Titel (split an " — ")
    # Sammle unique prefixes und suffixes
    local prefixes_json
    prefixes_json=$(echo "$titles_json" | jq -r '
      [.[] | split(" — ") | .[0]] | unique
    ')
    local suffixes_json
    suffixes_json=$(echo "$titles_json" | jq -r '
      [.[] | split(" — ") | (if length > 1 then .[1] else empty end)] | unique
    ')

    local prefixes_count
    prefixes_count=$(echo "$prefixes_json" | jq -r 'length')
    local suffixes_count
    suffixes_count=$(echo "$suffixes_json" | jq -r 'length')

    # Heuristik: Finde den "besten" Komponenten-Namen
    local component_name=""

    if [[ "$prefixes_count" -eq 1 ]]; then
      # Ein Prefix → verwende es als Komponenten-Name
      component_name=$(echo "$prefixes_json" | jq -r '.[0]')

      # Wenn der Prefix "SystemModule" oder generisch ist und die Datei anders heißt,
      # verwende lieber den Dateinamen als Fallback
      if [[ "$component_name" == "SystemModule" && "$base_name" != "SystemModule" ]]; then
        # Nimm den ersten Suffix als Komponenten-Namen falls vorhanden
        local first_suffix
        first_suffix=$(echo "$suffixes_json" | jq -r '.[0] // ""')
        if [[ -n "$first_suffix" && "$first_suffix" != "null" ]]; then
          component_name="$first_suffix"
          # Entferne diesen Suffix aus der Liste, da er jetzt der Komponenten-Name ist
          suffixes_json=$(echo "$suffixes_json" | jq -r '.[1:]')
          suffixes_count=$(echo "$suffixes_json" | jq -r 'length')
        else
          component_name="$base_name"
        fi
      fi
    else
      # Mehrere unterschiedliche Prefixes → liste sie alle (z.B. SystemSubComponents)
      component_name=$(echo "$prefixes_json" | jq -r 'join(", ")')
    fi

    # Baue Komponenten-Spalte
    if [[ "$suffixes_count" -gt 0 ]]; then
      local suffix_list
      suffix_list=$(echo "$suffixes_json" | jq -r 'join(", ")')
      komponenten_col="${component_name} (${suffix_list})"
    else
      komponenten_col="${component_name}"
    fi

    table+="| ${index} | \`${filename}\` | ${test_count} | ${komponenten_col} |\n"
    total_tests=$((total_tests + test_count))
    index=$((index + 1))
  done < <(echo "$VITEST_JSON" | jq -r '
    .testResults
    | sort_by(.name | split("/") | .[-1])
    | .[]
    | [
        (.name | split("/") | .[-1]),
        (.assertionResults | length),
        ([.assertionResults[].ancestorTitles[0]] | unique | join("\u0001"))
      ]
    | @tsv
  ')

  # Footer-Zeile
  table+="| **Gesamt** | | **${total_tests}** | |\n"

  echo -e "$table"
}

TABLE_MD=$(generate_table)

# ─── Ausgabe-Modus ────────────────────────────────────────────────────────────
case "$MODE" in
  --stdout)
    echo ""
    echo -e "${CYAN}${BOLD}## Test-Datei-Tabelle (generiert $(date '+%Y-%m-%d %H:%M'))${NC}"
    echo ""
    echo -e "$TABLE_MD"
    echo "> **Gesamtstatistik:** ${NUM_TOTAL} Tests — ${NUM_PASSED} passed, ${NUM_FAILED} failed"
    echo ""
    ;;

  --update)
    if [[ ! -f "$README_CI" ]]; then
      echo -e "${RED}❌ README.ci.md nicht gefunden: $README_CI${NC}" >&2
      exit 1
    fi

    # Erstelle eine temporäre Datei mit der neuen Tabelle
    TEMP_TABLE=$(mktemp)
    echo -e "$TABLE_MD" > "$TEMP_TABLE"

    # Finde die Test-Dateien Sektion in README.ci.md und ersetze sie
    # Die Sektion beginnt mit "**Test-Dateien (Gesamt:" und endet vor "> **Historie:**"
    START_MARKER="\*\*Test-Dateien (Gesamt:"
    END_MARKER="> \*\*Historie:\*\*"

    # Prüfe ob die Marker existieren
    if ! grep -q "$START_MARKER" "$README_CI"; then
      echo -e "${YELLOW}⚠️  Konnte Start-Marker nicht finden. Erstelle Backup und füge Tabelle ein.${NC}" >&2
      cp "$README_CI" "${README_CI}.bak"
      echo -e "\n## Test-Dateien (Gesamt: ${NUM_TOTAL} Tests, Stand: $(date '+%Y-%m-%d'))\n" >> "$README_CI"
      cat "$TEMP_TABLE" >> "$README_CI"
    else
      # Extrahiere Zeilennummern
      START_LINE=$(grep -n "$START_MARKER" "$README_CI" | head -1 | cut -d: -f1)
      END_LINE=$(grep -n "$END_MARKER" "$README_CI" | head -1 | cut -d: -f1)

      if [[ -z "$END_LINE" ]]; then
        # Fallback: ersetze ab Start-Marker bis zur nächsten Überschrift
        END_LINE=$(tail -n +"$START_LINE" "$README_CI" | grep -n "^>" | head -1 | cut -d: -f1)
        END_LINE=$((START_LINE + END_LINE - 1))
      fi

      if [[ -n "$START_LINE" && -n "$END_LINE" ]]; then
        # Aktualisiere den Header der Test-Dateien-Zeile
        NEW_HEADER="**Test-Dateien (Gesamt: ${NUM_TOTAL} Tests, Stand: $(date '+%Y-%m-%d')):**"
        # Erstelle neue README.ci.md
        {
          head -n $((START_LINE - 1)) "$README_CI"
          echo "$NEW_HEADER"
          echo ""
          cat "$TEMP_TABLE"
          tail -n +$((END_LINE + 1)) "$README_CI"
        } > "${README_CI}.new"

        mv "${README_CI}.new" "$README_CI"
        echo -e "${GREEN}✅ README.ci.md aktualisiert (${NUM_TOTAL} Tests, $(date '+%Y-%m-%d'))${NC}" >&2
      else
        echo -e "${RED}❌ Konnte Tabellen-Bereich in README.ci.md nicht lokalisieren${NC}" >&2
        rm "$TEMP_TABLE"
        exit 1
      fi
    fi

    rm -f "$TEMP_TABLE"
    ;;

  --check)
    if [[ ! -f "$README_CI" ]]; then
      echo -e "${RED}❌ README.ci.md nicht gefunden${NC}" >&2
      exit 1
    fi

    # Extrahiere aktuelle Test-Zahl aus README.ci.md
    DOC_TOTAL=$(grep -oP '\*\*Test-Dateien \(Gesamt: \K[0-9]+' "$README_CI" 2>/dev/null || echo "0")

    if [[ "$DOC_TOTAL" != "$NUM_TOTAL" ]]; then
      echo -e "${RED}❌ README.ci.md nicht aktuell: Dokumentiert=${DOC_TOTAL}, Aktuell=${NUM_TOTAL}${NC}" >&2
      echo ""
      echo -e "$TABLE_MD"
      exit 1
    else
      echo -e "${GREEN}✅ README.ci.md aktuell: ${NUM_TOTAL} Tests${NC}" >&2
      exit 0
    fi
    ;;

  *)
    echo -e "${RED}Unbekannter Modus: $MODE${NC}" >&2
    echo "Usage: $0 [--stdout|--update|--check]" >&2
    exit 1
    ;;
esac

exit 0
