#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – healthcheck.sh
# Überprüft den Zustand aller Kirobi-Dienste
# =============================================================================
set -uo pipefail

OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OPENWEBUI_PORT="${OPENWEBUI_PORT:-3000}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
FLOWISE_PORT="${FLOWISE_PORT:-3001}"

PASS=0
FAIL=0

check_http() {
  local name="$1"
  local url="$2"
  local expected_code="${3:-200}"
  
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "$url" 2>/dev/null || echo "000")
  
  if [ "$code" = "$expected_code" ]; then
    echo "  ✅ $name ($url) → HTTP $code"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $name ($url) → HTTP $code (erwartet: $expected_code)"
    FAIL=$((FAIL + 1))
  fi
}

check_tcp() {
  local name="$1"
  local host="$2"
  local port="$3"
  
  if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
    echo "  ✅ $name (TCP $host:$port)"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $name (TCP $host:$port) nicht erreichbar"
    FAIL=$((FAIL + 1))
  fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Kirobi / Disruptive OS – Healthcheck"
echo "  $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "→ Datenbank-Services:"
check_tcp "PostgreSQL" "localhost" "$POSTGRES_PORT"
check_http "Qdrant REST" "http://localhost:$QDRANT_PORT/collections"
check_http "Qdrant Health" "http://localhost:$QDRANT_PORT/healthz"

echo ""
echo "→ KI-Services:"
check_http "Ollama API" "http://localhost:$OLLAMA_PORT/api/tags"

echo ""
echo "→ Interface-Services:"
check_http "Open WebUI" "http://localhost:$OPENWEBUI_PORT"
check_http "Flowise" "http://localhost:$FLOWISE_PORT"

echo ""
echo "→ External-Agents (optional, Profile external-agents):"
HERMES_RUNTIME_PORT="${HERMES_RUNTIME_PORT:-9119}"
OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
if timeout 1 bash -c "echo >/dev/tcp/localhost/$HERMES_RUNTIME_PORT" 2>/dev/null; then
  check_http "Hermes Dashboard" "http://localhost:$HERMES_RUNTIME_PORT/"
else
  echo "  ⏭️  Hermes Runtime (Port $HERMES_RUNTIME_PORT nicht offen — Profile external-agents nicht aktiv?)"
fi
if timeout 1 bash -c "echo >/dev/tcp/localhost/$OPENCLAW_GATEWAY_PORT" 2>/dev/null; then
  check_http "OpenClaw Health" "http://localhost:$OPENCLAW_GATEWAY_PORT/healthz"
else
  echo "  ⏭️  OpenClaw Gateway (Port $OPENCLAW_GATEWAY_PORT nicht offen — Profile external-agents nicht aktiv?)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Ergebnis: $PASS bestanden, $FAIL fehlgeschlagen"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "⚠️ Hinweis: Services mit Fehlern können nicht erreichbar sein."
  echo "  Prüfe mit: docker compose ps"
  echo "  Logs mit:  docker compose logs [service-name]"
  exit 1
fi
