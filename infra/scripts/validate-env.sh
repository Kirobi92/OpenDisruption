#!/usr/bin/env bash
# =============================================================================
# validate-env.sh — verify that .env is complete, well-formed, and safe.
# =============================================================================
# Exits 0 on success, 1 on hard failure, 2 on warnings only.
# Flags: --fix (interactively offer to inject missing keys from .env.example)
#        --quiet
# =============================================================================
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="$ROOT/.env"
EXAMPLE="$ROOT/.env.example"

FIX=0; QUIET=0
for a in "$@"; do
  case "$a" in
    --fix)   FIX=1 ;;
    --quiet) QUIET=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  esac
done

if [[ -t 1 ]] && [[ "${NO_COLOR:-}" != "1" ]]; then
  R=$'\e[31m'; G=$'\e[32m'; Y=$'\e[33m'; B=$'\e[34m'; N=$'\e[0m'
else R=""; G=""; Y=""; B=""; N=""; fi
say()  { (( QUIET )) || printf '%s%s%s\n' "$B" "$*" "$N"; }
ok()   { (( QUIET )) || printf '%s✔%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s⚠%s %s\n' "$Y" "$N" "$*" >&2; }
err()  { printf '%s✖%s %s\n' "$R" "$N" "$*" >&2; }

[[ -f "$ENV_FILE" ]]   || { err ".env not found at $ENV_FILE — run install.sh."; exit 1; }
[[ -f "$EXAMPLE" ]]    || { err ".env.example missing — repo corrupt."; exit 1; }

# 1. permission check
if [[ "$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%A' "$ENV_FILE")" != "600" ]]; then
  warn ".env is not chmod 600 (running: chmod 600 $ENV_FILE)"
  chmod 600 "$ENV_FILE" || true
fi

# 2. parse & build sets
declare -A IN_ENV IN_EXAMPLE
while IFS='=' read -r k v; do
  [[ "$k" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${k// }" ]] && continue
  IN_ENV["$k"]="$v"
done < <(grep -E '^[A-Z][A-Z0-9_]*=' "$ENV_FILE" || true)

while IFS='=' read -r k v; do
  [[ "$k" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${k// }" ]] && continue
  IN_EXAMPLE["$k"]="$v"
done < <(grep -E '^[A-Z][A-Z0-9_]*=' "$EXAMPLE" || true)

# 3. missing keys
MISSING=()
for k in "${!IN_EXAMPLE[@]}"; do
  if [[ -z "${IN_ENV[$k]+x}" ]]; then MISSING+=("$k"); fi
done

WARN_COUNT=0; FAIL_COUNT=0
say "Checking $ENV_FILE against $EXAMPLE"

if (( ${#MISSING[@]} )); then
  for k in "${MISSING[@]}"; do warn "missing key: $k"; ((++WARN_COUNT)); done
  if (( FIX )); then
    say "Appending missing keys from .env.example"
    {
      echo ""
      echo "# --- appended by validate-env.sh on $(date -u +%FT%TZ) ---"
      for k in "${MISSING[@]}"; do echo "${k}=${IN_EXAMPLE[$k]}"; done
    } >>"$ENV_FILE"
    ok "appended ${#MISSING[@]} key(s); please re-run validate-env.sh"
  fi
fi

# 4. placeholder secrets
PLACEHOLDER_KEYS=()
for k in "${!IN_ENV[@]}"; do
  if [[ "${IN_ENV[$k]}" == *"AENDERE_DIESEN_SCHLUESSEL"* ]] \
  || [[ "${IN_ENV[$k]}" == "changeme" ]] \
  || [[ "${IN_ENV[$k]}" == "changeme-in-production" ]]; then
    PLACEHOLDER_KEYS+=("$k")
  fi
done
if (( ${#PLACEHOLDER_KEYS[@]} )); then
  for k in "${PLACEHOLDER_KEYS[@]}"; do err "placeholder secret still present: $k"; ((++FAIL_COUNT)); done
fi

# 5. weak secrets (<24 chars) for *_SECRET / *_PASSWORD / JWT_SECRET_KEY
for k in "${!IN_ENV[@]}"; do
  if [[ "$k" == *SECRET* || "$k" == *PASSWORD* || "$k" == *KEY* ]] \
     && [[ -n "${IN_ENV[$k]}" ]] \
     && (( ${#IN_ENV[$k]} < 24 )); then
    warn "weak secret (<24 chars): $k"
    ((++WARN_COUNT))
  fi
done

# 6. coherence
[[ "${IN_ENV[KIROBI_BIND_HOST]:-127.0.0.1}" == "0.0.0.0" ]] && \
  warn "KIROBI_BIND_HOST=0.0.0.0 → services exposed on every interface"
[[ "${IN_ENV[KIROBI_ENV]:-development}" == "production" ]] && \
  [[ "${IN_ENV[KIROBI_LOG_LEVEL]:-info}" == "debug" ]] && \
  warn "KIROBI_ENV=production but KIROBI_LOG_LEVEL=debug"

# 7. summary
say "─── summary ───"
ok "checked ${#IN_EXAMPLE[@]} expected key(s); env defines ${#IN_ENV[@]}"
(( WARN_COUNT > 0 )) && warn "$WARN_COUNT warning(s)"
(( FAIL_COUNT > 0 )) && err  "$FAIL_COUNT failure(s)"

if (( FAIL_COUNT )); then exit 1; fi
if (( WARN_COUNT )); then exit 2; fi
ok "environment valid"
exit 0
