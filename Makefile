# =============================================================================
# Kirobi / Disruptive OS – Makefile
# =============================================================================

COMPOSE = docker compose
COMPOSE_FILE = docker-compose.yml
ENV_FILE = .env

.PHONY: help up down restart logs pull-models init status backup clean build

## Hilfe anzeigen
help:
@echo ""
@echo "Kirobi / Disruptive OS – Verfügbare Befehle:"
@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
@echo "  make init         – System initialisieren (erste Einrichtung)"
@echo "  make up           – Alle Services starten"
@echo "  make down         – Alle Services stoppen"
@echo "  make restart      – Alle Services neu starten"
@echo "  make status       – Status aller Services anzeigen"
@echo "  make logs         – Logs aller Services (follow)"
@echo "  make pull-models  – Ollama-Modelle herunterladen"
@echo "  make backup       – Backup erstellen"
@echo "  make clean        – Ungenutzte Docker-Ressourcen aufräumen"
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
