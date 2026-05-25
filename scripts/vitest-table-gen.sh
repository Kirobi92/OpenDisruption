#!/usr/bin/env bash
# ==============================================================================
# vitest-table-gen.sh — Parse vitest --reporter=json output and generate
# a test-file overview table for README.ci.md.
#
# Usage:
#   vitest-table-gen.sh --check                          # Compare vs README.ci.md, exit 1 on drift
#   vitest-table-gen.sh --update                         # Rewrite README.ci.md test table section
#   vitest-table-gen.sh --update --input-file <path>     # Use custom JSON input
#   vitest-table-gen.sh --output-table                   # Print table to stdout only
#
# Exit codes:
#   0 — OK / no drift
#   1 — Drift detected (--check) or parse error
#   2 — Missing input file or README.ci.md
# ==============================================================================

set -euo pipefail

# ─── Defaults ────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_FILE="$REPO_ROOT/frontend/vitest-results.json"
README_FILE="$REPO_ROOT/README.ci.md"
MODE=""
OUTPUT_TABLE_ONLY=false

# ─── Parse Arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --check)
            MODE="check"
            shift
            ;;
        --update)
            MODE="update"
            shift
            ;;
        --output-table)
            OUTPUT_TABLE_ONLY=true
            shift
            ;;
        --input-file)
            INPUT_FILE="$2"
            shift 2
            ;;
        --readme)
            README_FILE="$2"
            shift 2
            ;;
        -h|--help)
            cat << 'EOF'
Usage: vitest-table-gen.sh [OPTIONS]

Parse vitest --reporter=json output and sync a test-file overview table
into README.ci.md.

OPTIONS:
  --check               Dry-run: compare generated table with current
                        README.ci.md, exit 1 on drift.
  --update              Rewrite the test-file table section in README.ci.md.
  --output-table        Print generated table to stdout only.
  --input-file PATH     Path to vitest-results.json
                        (default: frontend/vitest-results.json)
  --readme PATH         Path to README.ci.md
                        (default: README.ci.md in repo root)
  -h, --help            Show this help.

EXIT CODES:
  0 — OK / no drift
  1 — Drift detected (--check) or parse error
  2 — Missing input file or README.ci.md

EXAMPLES:
  # Check if README.ci.md matches current vitest results:
  scripts/vitest-table-gen.sh --check

  # Update README.ci.md after running vitest:
  scripts/vitest-table-gen.sh --update

  # Use a pre-generated JSON file:
  scripts/vitest-table-gen.sh --update --input-file frontend/vitest-results.json
EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1" >&2
            echo "Usage: vitest-table-gen.sh [--check|--update] [--input-file PATH]" >&2
            exit 1
            ;;
    esac
done

# ─── Validierung ─────────────────────────────────────────────────────────────
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "ERROR: vitest-results.json not found at: $INPUT_FILE" >&2
    echo "Run: cd frontend && npx vitest run --reporter=json > vitest-results.json" >&2
    exit 2
fi

if [[ "$MODE" == "update" ]] && [[ ! -f "$README_FILE" ]]; then
    echo "ERROR: README.ci.md not found at: $README_FILE" >&2
    exit 2
fi

if [[ "$MODE" == "check" ]] && [[ ! -f "$README_FILE" ]]; then
    echo "WARNING: README.ci.md not found at: $README_FILE — assuming drift" >&2
    echo "DRIFT: README.ci.md missing" >&2
    exit 1
fi

# ─── Parse JSON ──────────────────────────────────────────────────────────────
if ! command -v jq &>/dev/null; then
    echo "ERROR: jq is required but not installed." >&2
    exit 1
fi

# Extract test results: per-file name, test count, passed/failed
# vitest --reporter=json format:
# {
#   "numTotalTests": N,
#   "numPassedTests": N,
#   "numFailedTests": N,
#   "testResults": [
#     {
#       "name": "/abs/path/to/file.test.tsx",
#       "status": "passed"|"failed",
#       "assertionResults": [...]
#     }
#   ]
# }

TOTAL_TESTS=$(jq -r '.numTotalTests // 0' "$INPUT_FILE")
readonly TOTAL_TESTS
PASSED_TESTS=$(jq -r '.numPassedTests // 0' "$INPUT_FILE")
readonly PASSED_TESTS
FAILED_TESTS=$(jq -r '.numFailedTests // 0' "$INPUT_FILE")
readonly FAILED_TESTS
NUM_FILES=$(jq -r '.testResults | length // 0' "$INPUT_FILE")
readonly NUM_FILES

# Build per-file data
FILE_DATA=$(jq -r '
    .testResults // [] | to_entries | .[] |
    [
        (.key + 1 | tostring),                          # row number
        (.value.name | sub(".*/frontend/"; "")),        # relative path
        (.value.assertionResults | length | tostring),   # test count
        (if .value.status == "passed" then "✅" else "❌" end)  # status
    ] | join("|")
' "$INPUT_FILE")
readonly FILE_DATA

# ─── Generate Table ──────────────────────────────────────────────────────────
generate_table() {
    local total="$1"
    local passed="$2"
    local failed="$3"
    local num_files="$4"
    local file_data="$5"

    cat << TABLE_END
> **Automatisch generiert** via \`scripts/vitest-table-gen.sh --update\` — Stand: $(date -u +"%Y-%m-%d %H:%M UTC")

| Gesamt-Tests | Bestanden | Fehlgeschlagen | Test-Dateien |
|---|---:|---:|---:|
| $total | $passed | $failed | $num_files |

### Test-Datei-Übersicht

| # | Test-Datei | Tests | Status |
|---|---|---|---|
TABLE_END

    if [[ -n "$file_data" ]]; then
        echo "$file_data" | while IFS= read -r line; do
            echo "| $line |"
        done
    else
        echo "| — | *Keine Test-Dateien gefunden* | 0 | — |"
    fi

    echo ""
}

GENERATED_TABLE=$(generate_table "$TOTAL_TESTS" "$PASSED_TESTS" "$FAILED_TESTS" "$NUM_FILES" "$FILE_DATA")
readonly GENERATED_TABLE

# ─── Modes ───────────────────────────────────────────────────────────────────

if $OUTPUT_TABLE_ONLY; then
    echo "$GENERATED_TABLE"
    exit 0
fi

# Marker-Tags in README.ci.md
readonly START_MARKER="<!-- VITEST-TABLE-START -->"
readonly END_MARKER="<!-- VITEST-TABLE-END -->"

# Generate the full markdown block to insert
readonly TABLE_BLOCK="${START_MARKER}
${GENERATED_TABLE}
${END_MARKER}"

if [[ "$MODE" == "check" ]]; then
    # Extract the current table section from README.ci.md
    CURRENT_BLOCK=$(sed -n "/^${START_MARKER}/,/^${END_MARKER}/p" "$README_FILE" 2>/dev/null || echo "")

    if [[ -z "$CURRENT_BLOCK" ]]; then
        echo "DRIFT: No vitest table markers found in README.ci.md" >&2
        echo "Add markers: ${START_MARKER} ... ${END_MARKER}" >&2
        exit 1
    fi

    # Normalize and compare (strip trailing whitespace, unify line endings)
    CURRENT_NORMALIZED=$(echo "$CURRENT_BLOCK" | sed 's/[[:space:]]*$//')
    NEW_NORMALIZED=$(echo "$TABLE_BLOCK" | sed 's/[[:space:]]*$//')

    if [[ "$CURRENT_NORMALIZED" != "$NEW_NORMALIZED" ]]; then
        echo "DRIFT: Test table in README.ci.md is out of date." >&2
        echo "Run: scripts/vitest-table-gen.sh --update" >&2

        # Show diff for troubleshooting
        diff <(echo "$CURRENT_NORMALIZED") <(echo "$NEW_NORMALIZED") >&2 || true

        exit 1
    fi

    echo "OK: Test table in README.ci.md matches vitest results (${TOTAL_TESTS} tests, ${NUM_FILES} files)."
    exit 0
fi

if [[ "$MODE" == "update" ]]; then
    # Check if markers already exist
    if grep -q "^${START_MARKER}" "$README_FILE" 2>/dev/null; then
        # Replace existing table block between markers
        # Use a temp file approach for reliability
        _tmp_file=$(mktemp)
        _in_block=false

        while IFS= read -r line; do
            if [[ "$line" == "${START_MARKER}" ]]; then
                _in_block=true
                echo "$TABLE_BLOCK" >> "$_tmp_file"
                continue
            fi
            if [[ "$line" == "${END_MARKER}" ]]; then
                _in_block=false
                continue
            fi
            if ! $_in_block; then
                echo "$line" >> "$_tmp_file"
            fi
        done < "$README_FILE"

        mv "$_tmp_file" "$README_FILE"
        echo "OK: Updated existing vitest table in README.ci.md"
    else
        # No markers yet — append table at the end with markers
        echo "" >> "$README_FILE"
        echo "---" >> "$README_FILE"
        echo "" >> "$README_FILE"
        echo "$TABLE_BLOCK" >> "$README_FILE"
        echo "OK: Appended vitest table to README.ci.md (no existing markers found)"
    fi

    echo "   Tests: ${TOTAL_TESTS} total | ${PASSED_TESTS} passed | ${FAILED_TESTS} failed | ${NUM_FILES} files"
    exit 0
fi

# If no mode specified, default to --check with a helpful message
echo "INFO: No mode specified. Use --check, --update, or --output-table." >&2
echo "Running in check mode by default..." >&2
# Re-run as check
exec "$0" --check --input-file "$INPUT_FILE" --readme "$README_FILE"
