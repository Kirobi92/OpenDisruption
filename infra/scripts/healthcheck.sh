#!/usr/bin/env bash
# =============================================================================
# Kirobi / Disruptive OS – healthcheck.sh
# Überprüft den Zustand aller 29 Kirobi-Dienste
# Verwendung: bash infra/scripts/healthcheck.sh [--json] [--quiet]
# =============================================================================
set -uo pipefail

QUIET=0
JSON=0
for arg in "${@:-}"; do
  case "$arg" in
    --quiet|-q) QUIET=1 ;;
    --json)     JSON=1 ;;
  esac
done

# ── Port-Defaults (aus .env überschreibbar) ──────────────────────────────────
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
OPENWEBUI_PORT="${OPENWEBUI_PORT:-3000}"
FLOWISE_PORT="${FLOWISE_PORT:-3001}"
VOICE_PROC_PORT="${VOICE_PROC_PORT:-8001}"
AUTH_PORT="${AUTH_PORT:-8002}"
API_PORT="${API_PORT:-8003}"
EMBEDDINGS_PORT="${EMBEDDINGS_PORT:-8004}"
RETRIEVAL_PORT="${RETRIEVAL_PORT:-8006}"
INGEST_PORT="${INGEST_PORT:-8007}"
MODEL_ROUTING_PORT="${MODEL_ROUTING_PORT:-8009}"
ANALYTICS_PORT="${ANALYTICS_PORT:-8010}"
IMAGE_GEN_PORT="${IMAGE_GEN_PORT:-8011}"
MEDIA_PROC_PORT="${MEDIA_PROC_PORT:-8012}"
MUSIC_GEN_PORT="${MUSIC_GEN_PORT:-8013}"
VIDEO_GEN_PORT="${VIDEO_GEN_PORT:-8014}"
NUTZI_PORT="${NUTZI_PORT:-8016}"
WEB_PORT="${WEB_PORT:-3002}"
DASHBOARD_PORT="${DASHBOARD_PORT:-3003}"
VOICE_APP_PORT="${VOICE_APP_PORT:-3004}"
ADMIN_PORT="${ADMIN_PORT:-3005}"
PORTAL_PORT="${PORTAL_PORT:-3006}"
WEB_SVELTE_PORT="${WEB_SVELTE_PORT:-3007}"
HERMES_RUNTIME_PORT="${HERMES_RUNTIME_PORT:-9119}"
OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"

PASS=0
FAIL=0
WARN=0
RESULTS=()

check_http() {
  local name="$1" url="$2" expected_code="${3:-200}"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "$expected_code" ]; then
    [ "$QUIET" -eq 0 ] && echo "  ✅ $name → HTTP $code"
    PASS=$((PASS + 1))
    RESULTS+=("{\"name\":\"$name\",\"status\":\"ok\",\"code\":$code}")
  else
    [ "$QUIET" -eq 0 ] && echo "  ❌ $name ($url) → HTTP $code (erwartet: $expected_code)"
    FAIL=$((FAIL + 1))
    RESULTS+=("{\"name\":\"$name\",\"status\":\"fail\",\"code\":$code,\"url\":\"$url\"}")
  fi
}

check_tcp() {
  local name="$1" host="$2" port="$3"
  if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
    [ "$QUIET" -eq 0 ] && echo "  ✅ $name (TCP $host:$port)"
    PASS=$((PASS + 1))
    RESULTS+=("{\"name\":\"$name\",\"status\":\"ok\"}")
  else
    [ "$QUIET" -eq 0 ] && echo "  ❌ $name (TCP $host:$port)"
    FAIL=$((FAIL + 1))
    RESULTS+=("{\"name\":\"$name\",\"status\":\"fail\",\"url\":\"tcp://$host:$port\"}")
  fi
}

check_optional() {
  local name="$1" url="$2" port="$3"
  if timeout 1 bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
    check_http "$name" "$url"
  else
    [ "$QUIET" -eq 0 ] && echo "  ⏭️  $name (Port $port nicht offen — optional)"
    WARN=$((WARN + 1))
    RESULTS+=("{\"name\":\"$name\",\"status\":\"skip\"}")
  fi
}

check_docker_health() {
  local name="$1" container="$2"
  local state
  state=$(docker inspect --format '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
  case "$state" in
    healthy)
      [ "$QUIET" -eq 0 ] && echo "  ✅ $name (Docker: healthy)"
      PASS=$((PASS + 1))
      RESULTS+=("{\"name\":\"$name\",\"status\":\"ok\",\"docker\":\"healthy\"}")
      ;;
    unhealthy)
      [ "$QUIET" -eq 0 ] && echo "  ❌ $name (Docker: unhealthy)"
      FAIL=$((FAIL + 1))
      RESULTS+=("{\"name\":\"$name\",\"status\":\"fail\",\"docker\":\"unhealthy\"}")
      ;;
    starting)
      [ "$QUIET" -eq 0 ] && echo "  🔄 $name (Docker: starting)"
      WARN=$((WARN + 1))
      RESULTS+=("{\"name\":\"$name\",\"status\":\"starting\",\"docker\":\"starting\"}")
      ;;
    none)
      [ "$QUIET" -eq 0 ] && echo "  ⏭️  $name (kein Docker-Healthcheck definiert)"
      WARN=$((WARN + 1))
      RESULTS+=("{\"name\":\"$name\",\"status\":\"skip\"}")
      ;;
  esac
}

# ── Header ───────────────────────────────────────────────────────────────────
if [ "$QUIET" -eq 0 ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Kirobi / Disruptive OS – Vollständiger Healthcheck"
  echo "  $(date '+%Y-%m-%d %H:%M:%S')"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
fi

# ── Infrastruktur ────────────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo "→ Infrastruktur:"
check_tcp  "PostgreSQL"        "localhost" "$POSTGRES_PORT"
check_http "Qdrant"            "http://localhost:$QDRANT_PORT/healthz"
check_http "Ollama"            "http://localhost:$OLLAMA_PORT/api/tags"

# ── Core API-Services ────────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo ""
[ "$QUIET" -eq 0 ] && echo "→ Core API-Services:"
check_http "Auth"              "http://localhost:$AUTH_PORT/health"
check_http "API"               "http://localhost:$API_PORT/health"
check_http "Embeddings"        "http://localhost:$EMBEDDINGS_PORT/health"
check_http "Retrieval"         "http://localhost:$RETRIEVAL_PORT/health"
check_http "Ingest"            "http://localhost:$INGEST_PORT/health"
check_http "Analytics"         "http://localhost:$ANALYTICS_PORT/health"
check_http "Model-Routing"     "http://localhost:$MODEL_ROUTING_PORT/health"

# ── KI-Generierung ───────────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo ""
[ "$QUIET" -eq 0 ] && echo "→ KI-Generierungs-Services:"
check_http "Voice-Processing"  "http://localhost:$VOICE_PROC_PORT/health"
check_http "Image-Generation"  "http://localhost:$IMAGE_GEN_PORT/health"
check_http "Media-Processing"  "http://localhost:$MEDIA_PROC_PORT/health"
check_http "Music-Generation"  "http://localhost:$MUSIC_GEN_PORT/health"
check_http "Video-Generation"  "http://localhost:$VIDEO_GEN_PORT/health"
check_http "Nutzi (eNVenta)"   "http://localhost:$NUTZI_PORT/health"

# ── Frontends ────────────────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo ""
[ "$QUIET" -eq 0 ] && echo "→ Frontends:"
check_http "Open WebUI"        "http://localhost:$OPENWEBUI_PORT"
check_http "Flowise"           "http://localhost:$FLOWISE_PORT"
check_http "Web PWA"           "http://localhost:$WEB_PORT"
check_http "Dashboard"         "http://localhost:$DASHBOARD_PORT"
check_http "Voice App"         "http://localhost:$VOICE_APP_PORT"
check_http "Admin UI"          "http://localhost:$ADMIN_PORT"
check_http "User Portal"       "http://localhost:$PORTAL_PORT"
check_http "Web Svelte"        "http://localhost:$WEB_SVELTE_PORT/v2/login"
check_http "Caddy (Proxy)"     "http://localhost:80"

# ── Agenten & Gateways ───────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo ""
[ "$QUIET" -eq 0 ] && echo "→ Agenten & Gateways:"
check_http "Hermes Runtime"    "http://localhost:$HERMES_RUNTIME_PORT/"
check_optional "OpenClaw"      "http://localhost:$OPENCLAW_GATEWAY_PORT/healthz" "$OPENCLAW_GATEWAY_PORT"

# ── Disk ─────────────────────────────────────────────────────────────────────
[ "$QUIET" -eq 0 ] && echo ""
[ "$QUIET" -eq 0 ] && echo "→ Systemressourcen:"
DISK_PCT=$(df / --output=pcent | tail -1 | tr -dc '0-9')
DISK_FREE=$(df -h / --output=avail | tail -1 | tr -d ' ')
if [ "$DISK_PCT" -lt 90 ]; then
  [ "$QUIET" -eq 0 ] && echo "  ✅ Disk / → ${DISK_FREE} frei (${DISK_PCT}% belegt)"
  PASS=$((PASS + 1))
elif [ "$DISK_PCT" -lt 96 ]; then
  [ "$QUIET" -eq 0 ] && echo "  ⚠️  Disk / → ${DISK_FREE} frei (${DISK_PCT}% belegt) — knapp!"
  WARN=$((WARN + 1))
else
  [ "$QUIET" -eq 0 ] && echo "  ❌ Disk / → ${DISK_FREE} frei (${DISK_PCT}% belegt) — KRITISCH!"
  FAIL=$((FAIL + 1))
fi

# ── Ergebnis ─────────────────────────────────────────────────────────────────
if [ "$JSON" -eq 1 ]; then
  IFS=','; echo "{\"pass\":$PASS,\"fail\":$FAIL,\"warn\":$WARN,\"results\":[${RESULTS[*]}]}"
  unset IFS
else
  [ "$QUIET" -eq 0 ] && echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  ✅ $PASS OK  |  ❌ $FAIL Fehler  |  ⏭️  $WARN Übersprungen"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "  Logs:   docker compose logs [service]"
    echo "  Neustart: docker compose restart [service]"
    exit 1
  fi
fi
