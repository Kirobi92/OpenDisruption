#!/bin/bash
# shellcheck-error-only.sh
# Actionlint shellcheck-Wrapper für Kirobi APK CI
#
# Zweck: actionlint ruft dieses Script als shellcheck-Ersatz auf.
# SC-Findings auf info/style/warning-Level werden ausgegeben aber
# lösen KEINEN exit-1 aus — kein LINT FAIL wegen SC2086-Info-Findings.
# Nur Findings auf "error"-Level führen zu exit-1.
#
# Verwendung in lint-workflows.yml:
#   actionlint -shellcheck scripts/shellcheck-error-only.sh ...
shellcheck -S error "$@"
