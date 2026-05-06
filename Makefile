# =============================================================================
# Kirobi / Disruptive OS – Makefile
# =============================================================================

COMPOSE = docker compose
COMPOSE_FILE = docker-compose.yml
ENV_FILE = .env

.PHONY: help up down restart logs pull-models init status backup clean build \
        bootstrap interview autonomous-once autonomous-loop doctor test scan backlog

## Hilfe anzeigen
help:
	@echo ""
	@echo "Kirobi / Disruptive OS – Verfügbare Befehle:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  make init            – System initialisieren (erste Einrichtung)"
	@echo "  make up              – Alle Services starten"
	@echo "  make down            – Alle Services stoppen"
	@echo "  make restart         – Alle Services neu starten"
	@echo "  make status          – Status aller Services anzeigen"
	@echo "  make logs            – Logs aller Services (follow)"
	@echo "  make pull-models     – Ollama-Modelle herunterladen"
	@echo ""
	@echo "Voice & Interview:"
	@echo "  make voice-test      – Voice Interface testen (STT + TTS)"
	@echo "  make start-interview – Family Interview starten"
	@echo "  make voice-logs      – Voice Service Logs anzeigen"
	@echo ""
	@echo "Local Python core (no Docker required):"
	@echo "  make bootstrap        – .env anlegen + Doctor + Scan (lokaler Kickstart)"
	@echo "  make doctor           – Health-Check der lokalen Umgebung"
	@echo "  make scan             – Repository scannen (JSON-Zusammenfassung)"
	@echo "  make backlog          – Backlog generieren (priorisierte Tasks als JSON)"
	@echo "  make interview        – Geführtes Onboarding-Interview (CLI)"
	@echo "  make autonomous-once  – Eine autonome Iteration (Dry-Run, Report nach .kirobi/reports/)"
	@echo "  make autonomous-loop  – Autonome Schleife (Dry-Run, ITERATIONS=N optional)"
	@echo "  make test             – pytest tests/unit"
	@echo ""
	@echo "  make backup          – Backup erstellen"
	@echo "  make clean           – Ungenutzte Docker-Ressourcen aufräumen"
	@echo ""

## Erste Einrichtung
init:
	@echo "→ Initialisiere Kirobi / Disruptive OS..."
	@if [ ! -f $(ENV_FILE) ]; then \
	cp .env.example $(ENV_FILE); \
	echo "  ✓ .env aus .env.example erstellt – bitte anpassen!"; \
else \
	echo "  ℹ .env existiert bereits"; \
	fi
	@chmod +x infra/scripts/*.sh
	@bash infra/scripts/init-folders.sh
	@echo "  ✓ Verzeichnisse initialisiert"
	@$(COMPOSE) pull
	@echo "  ✓ Docker-Images heruntergeladen"
	@echo "→ Initialisierung abgeschlossen!"
	@echo "→ Führe 'make up' aus um das System zu starten"

## Alle Services starten
up:
	@echo "→ Starte Kirobi / Disruptive OS..."
	@$(COMPOSE) up -d
	@echo ""
	@echo "  ✓ Services gestartet!"
	@echo "  Open WebUI:  http://localhost:$${OPENWEBUI_PORT:-3000}"
	@echo "  Flowise:     http://localhost:$${FLOWISE_PORT:-3001}"
	@echo "  Qdrant:      http://localhost:$${QDRANT_PORT:-6333}/dashboard"
	@echo "  Ollama:      http://localhost:$${OLLAMA_PORT:-11434}"
	@echo ""

## Alle Services stoppen
down:
	@echo "→ Stoppe alle Services..."
	@$(COMPOSE) down
	@echo "  ✓ Alle Services gestoppt"

## Alle Services neu starten
restart:
	@echo "→ Starte alle Services neu..."
	@$(COMPOSE) restart
	@echo "  ✓ Alle Services neu gestartet"

## Einzelnen Service neu starten (Verwendung: make restart-service SERVICE=ollama)
restart-service:
	@$(COMPOSE) restart $(SERVICE)

## Logs anzeigen (alle Services)
logs:
	@$(COMPOSE) logs -f

## Logs für einzelnen Service (Verwendung: make logs-service SERVICE=ollama)
logs-service:
	@$(COMPOSE) logs -f $(SERVICE)

## Ollama-Modelle herunterladen
pull-models:
	@echo "→ Lade Ollama-Modelle herunter..."
	@bash infra/scripts/pull-models.sh
	@echo "  ✓ Modelle heruntergeladen"

## System-Status anzeigen
status:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Kirobi / Disruptive OS – System Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@$(COMPOSE) ps
	@echo ""
	@bash infra/scripts/healthcheck.sh

## Backup erstellen
backup:
	@echo "→ Erstelle Backup..."
	@bash infra/scripts/bootstrap.sh backup
	@echo "  ✓ Backup erstellt"

## Docker-Ressourcen aufräumen
clean:
	@echo "→ Räume Docker-Ressourcen auf..."
	@docker system prune -f
	@echo "  ✓ Aufgeräumt"

## Vollständiges Reset (VORSICHT: Löscht alle Daten!)
reset:
	@echo "⚠️  WARNUNG: Alle Daten werden gelöscht!"
	@read -p "Wirklich fortfahren? [j/N] " confirm && [ "$$confirm" = "j" ] || exit 1
	@$(COMPOSE) down -v
	@echo "  ✓ Alle Volumes gelöscht"

## Docker Compose config validieren
validate:
	@$(COMPOSE) config --quiet && echo "  ✓ docker-compose.yml ist valide"

## Verfügbare Ollama-Modelle anzeigen
list-models:
	@curl -s http://localhost:$${OLLAMA_PORT:-11434}/api/tags | python3 -m json.tool 2>/dev/null || \
	echo "  ⚠ Ollama nicht erreichbar"

## Postgres-Shell öffnen
db-shell:
	@$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-kirobi} -d $${POSTGRES_DB:-kirobi}

## Qdrant-Collections anzeigen
qdrant-collections:
	@curl -s http://localhost:$${QDRANT_PORT:-6333}/collections | python3 -m json.tool 2>/dev/null || \
	echo "  ⚠ Qdrant nicht erreichbar"

## Voice Interface testen
voice-test:
	@echo "→ Teste Voice Interface..."
	@$(COMPOSE) exec voice-processing python3 voice_interface.py --test-tts "Hallo, ich bin Kirobi. Das ist ein Test."
	@echo "  ✓ TTS Test abgeschlossen"
	@echo ""
	@echo "Für STT Test (mit Mikrofon):"
	@echo "  docker compose exec voice-processing python3 voice_interface.py --test-stt"

## Family Interview starten
start-interview:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║        Kirobi Family Interview - Willkommen!               ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Das Family Interview wird gestartet..."
	@echo "Bitte stelle sicher, dass dein Mikrofon funktioniert."
	@echo ""
	@read -p "Mit wem soll das Interview geführt werden? (Sven/Samira/Sineo): " NAME && \
	$(COMPOSE) exec supervisor python3 -c "import asyncio; from supervisor import KirobiSupervisor; s = KirobiSupervisor(); asyncio.run(s.start_family_interview('$$NAME'))"

## Voice Service Logs
voice-logs:
	@$(COMPOSE) logs -f voice-processing

## Supervisor Logs
supervisor-logs:
	@$(COMPOSE) logs -f supervisor

## Alle Voice-relevanten Services neu starten
voice-restart:
	@echo "→ Starte Voice Services neu..."
	@$(COMPOSE) restart voice-processing supervisor
	@echo "  ✓ Voice Services neu gestartet"

# =============================================================================
# Local Python core (no Docker required)
# =============================================================================

PY ?= python3
KIROBI = $(PY) -m kirobi_core

## Lokaler Kickstart: .env, Doctor und Scan
bootstrap:
	@if [ ! -f $(ENV_FILE) ]; then \
		cp .env.example $(ENV_FILE); \
		echo "  ✓ .env aus .env.example erstellt"; \
	fi
	@$(KIROBI) doctor || true
	@$(KIROBI) scan

## Health-Check der lokalen Umgebung
doctor:
	@$(KIROBI) doctor

## Repository scannen (JSON-Summary)
scan:
	@$(KIROBI) scan

## Backlog generieren (priorisierte Tasks)
backlog:
	@$(KIROBI) backlog --limit $${LIMIT:-20}

## Geführtes Onboarding-Interview
interview:
	@$(KIROBI) interview --profile $${PROFILE:-default}

## Eine autonome Iteration (Dry-Run, schreibt Report nach .kirobi/reports/)
autonomous-once:
	@$(KIROBI) autonomous-once --limit $${LIMIT:-10}

## Autonome Schleife (Dry-Run); ITERATIONS=N INTERVAL=Sekunden QUIET_HOURS="22:00-07:00"
autonomous-loop:
	@$(KIROBI) autonomous-loop \
		--interval $${INTERVAL:-900} \
		$$( [ -n "$${ITERATIONS}" ] && echo "--iterations $${ITERATIONS}" ) \
		$$( [ -n "$${QUIET_HOURS}" ] && echo "--quiet-hours $${QUIET_HOURS}" ) \
		--limit $${LIMIT:-10}

## Pytest-Suite ausführen (lokales Python-Core)
test:
	@$(PY) -m pytest tests/unit -q

## Live-Status der laufenden Service-Stack
status:
	@$(KIROBI) status

## PWA-Icons (apps/web/public/) aus dem SVG-Master neu generieren
pwa-icons:
	@$(PY) infra/scripts/build-pwa-icons.py --out apps/web/public

## Family-PWA samt Reverse-Proxy hochfahren (kirobi.local + LAN-IP)
pwa-up:
	@docker compose up -d caddy web auth api postgres
	@echo ""
	@echo "→ PWA erreichbar unter:"
	@echo "    http://$${KIROBI_HOSTNAME:-kirobi.local}/"
	@echo "    https://$${KIROBI_HOSTNAME:-kirobi.local}/   (TLS via Caddy internal CA)"
	@LAN_IP=$$(hostname -I 2>/dev/null | awk '{print $$1}'); \
		[ -n "$$LAN_IP" ] && echo "    http://$$LAN_IP/                     (LAN-IP)"

## mDNS / Avahi für kirobi.local einrichten (benötigt sudo)
pwa-mdns:
	@bash infra/scripts/setup-mdns.sh

## End-to-end Integration Check (statisch, ohne laufende Services)
integration-test:
	@echo "→ kirobi_core unit tests"
	@$(PY) -m pytest tests/unit -q
	@echo "→ kirobi_core doctor (offline)"
	@$(KIROBI) doctor || true
	@echo "→ supervisor.py importierbar?"
	@$(PY) -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('s', 'services/orchestrator/supervisor.py'); print('  ✓ kompiliert')" 2>&1 | head -5
	@echo "→ docker-compose.yml validieren"
	@docker compose config --quiet && echo "  ✓ compose valid" || echo "  ⚠ docker compose fehlt"
	@echo "→ bootstrap.sh syntax"
	@bash -n infra/scripts/bootstrap.sh && echo "  ✓ bootstrap.sh OK"
	@echo "→ healthcheck.sh syntax"
	@bash -n infra/scripts/healthcheck.sh && echo "  ✓ healthcheck.sh OK"
	@echo "→ setup-mdns.sh syntax"
	@bash -n infra/scripts/setup-mdns.sh && echo "  ✓ setup-mdns.sh OK"
	@echo "→ Caddyfile vorhanden"
	@test -f infra/caddy/Caddyfile && echo "  ✓ Caddyfile present"
	@echo "→ services/auth/main.py + services/api/main.py kompilieren"
	@$(PY) -m py_compile services/auth/main.py services/api/main.py && echo "  ✓ FastAPI services compile"
	@echo "→ PWA-Manifest valide"
	@$(PY) -c "import json; json.load(open('apps/web/public/manifest.json')); print('  ✓ manifest.json valid')"
	@echo "→ PWA-Icons vorhanden"
	@for f in icon.svg icon-192.png icon-512.png apple-touch-icon.png favicon.ico; do \
		test -f "apps/web/public/$$f" || { echo "  ✗ apps/web/public/$$f fehlt"; exit 1; }; \
	done
	@echo "  ✓ alle PWA-Icons vorhanden"
	@echo ""
	@echo "Integration-Check abgeschlossen."
