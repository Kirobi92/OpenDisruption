#!/usr/bin/env bash
# infra/scripts/daily-ai-research.sh
# Wrapper für daily-ai-research.py — lädt .env, aktiviert venv, loggt
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
LOG_DIR="${REPO_ROOT}/infra/logs"
LOG_FILE="${LOG_DIR}/daily-ai-research-$(date +%Y-%m-%d).log"

mkdir -p "${LOG_DIR}"

# .env laden
if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1090
    source <(grep -v '^#' "${REPO_ROOT}/.env" | grep '=')
    set +a
fi

export REPO_ROOT

# venv aktivieren
VENV="${REPO_ROOT}/.venv"
if [[ -d "${VENV}" ]]; then
    # shellcheck disable=SC1090
    source "${VENV}/bin/activate"
fi

echo "=== Kirobi Daily AI Research $(date '+%Y-%m-%d %H:%M:%S') ===" | tee -a "${LOG_FILE}"

exec python3 "${SCRIPT_DIR}/daily-ai-research.py" 2>&1 | tee -a "${LOG_FILE}"
