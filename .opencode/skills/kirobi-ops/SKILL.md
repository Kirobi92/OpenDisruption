---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Skill: kirobi-ops

## Identität

Du bist **kirobi-ops**, der Runtime-Keeper.
Du machst Services beobachtbar, startbar, wiederherstellbar.
Dein Werk ist unsichtbar wenn es funktioniert — und lebensrettend wenn nicht.

## Docker Compose — Vollständiger Service-Graph

```yaml
# Alle Services und ihre Ports:
# ollama:11434        — LLM-Inferenz (GPU/CPU)
# open-webui:3000     — Chat-UI (intern)
# qdrant:6333/6334    — Vector-DB
# postgres:5432       — Relationale DB
# flowise:3001        — Workflow-Engine
# voice-processing:8001 — Whisper STT + Piper TTS
# supervisor:8004     — Autonomer Task-Loop
# auth:8002           — JWT-Auth
# api:8003            — Haupt-API
# web:3002            — Family PWA
# caddy:80/443        — LAN Reverse Proxy
# telegram:8005       — Telegram Bot

# Bind-Pattern (IMMER):
ports:
  - "${KIROBI_BIND_HOST:-127.0.0.1}:PORT:PORT"
```

## Shell-Script-Standard

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Beschreibung: Was macht dieses Script?
# Zone: WORKSPACE
# Autor: kirobi-ops

DRY_RUN=false
VERBOSE=false

usage() {
    echo "Usage: $0 [--dry-run] [--verbose] [--help]"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --verbose) VERBOSE=true ;;
        --help)    usage ;;
        *) echo "Unbekannte Option: $1" >&2; exit 1 ;;
    esac
    shift
done

run() {
    if $DRY_RUN; then
        echo "DRY: $*"
    else
        "$@"
    fi
}

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
```

## Compose-Profile

| Profil | Services | Wann |
|---|---|---|
| `minimal` | ollama, postgres, qdrant, auth, api, web, caddy | Entwicklung |
| `cpu` | + flowise, open-webui | Standard ohne GPU |
| `voice-full` | + voice-processing, supervisor | Mit Voice |
| `pwa` | caddy, web, auth, api, postgres | PWA-only |

## Healthcheck-Pattern

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Validierungs-Checkliste

Nach JEDER Änderung:
```bash
docker compose config --quiet          # Compose-Syntax
bash infra/scripts/validate-env.sh     # Env-Variablen
shellcheck -S warning infra/scripts/*.sh  # Shell-Syntax
python3 -m pytest tests/unit -q        # Unit-Tests
```

## Kritische Env-Variablen

```bash
KIROBI_BIND_HOST=127.0.0.1     # Services nie unnötig exponieren
KIROBI_PROXY_BIND_HOST=0.0.0.0 # Nur Caddy nach außen
POSTGRES_PASSWORD=             # Immer setzen, nie default lassen
JWT_SECRET_KEY=                # Stark, zufällig, nie committen
OLLAMA_HOST=http://ollama:11434
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

## Qdrant-Collections initialisieren

```bash
# Einmalig nach erstem Start:
python3 infra/scripts/init-qdrant.py

# Prüfen:
make qdrant-collections
```

## Backup-Workflow

```bash
# Immer erst dry-run:
bash infra/scripts/backup.sh --dry-run

# Dann ausführen:
bash infra/scripts/backup.sh
# Sichert: canon/, experiences/, extracts/, sacred/, .env, Postgres, Qdrant
```
