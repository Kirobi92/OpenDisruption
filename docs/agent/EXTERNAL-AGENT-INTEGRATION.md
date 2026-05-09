---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-09
reviewed_by: pending
version: 1.0
---

# External Agent Integration — hermes-runtime, openclaw-gateway, aionui-cockpit

> **Phase 4.5 — paralleler Track.** ADR: `keycodi/decisions/0004-external-agent-integration.md`.
> Alle drei Tools laufen ausschliesslich gegen lokale Modelle (Ollama).

## Übersicht

| Tool | Rolle | Container | Port (lokal) | Caddy-Route |
|---|---|---|---|---|
| **hermes-runtime** | Skill-Hub + Reasoning + lokales Dashboard | `kirobi-hermes-runtime` | `127.0.0.1:9119` | `/hermes/*` |
| **openclaw-gateway** | Multi-Channel-Messaging-Bridge (Signal, WhatsApp, Discord, ...) | `kirobi-openclaw-gateway` | `127.0.0.1:18789/18790` | `/openclaw/*` |
| **aionui-cockpit** | Browser-Cockpit für CLI-Agents (Host-Install) | — (nativ) | `127.0.0.1:25808` | — |

## Erstinstallation

```bash
# 1. Submodules klonen (idempotent)
git submodule update --init --recursive external/hermes-agent external/openclaw

# 2. .env aus .env.example aktualisieren — neue Sektion "EXTERNAL AGENT TRACK"
diff .env.example .env | less

# 3. Container bauen + starten
make external-up        # baut + startet hermes-runtime + openclaw-gateway

# 4. AionUi-Cockpit auf Host installieren (Default --dry-run!)
make aionui-install                # Pre-Flight + Was-würde-passieren
make aionui-install APPLY=1        # tatsächlich installieren
```

> **Build-Zeit hermes-runtime:** beim ersten Mal 10+ Minuten (Playwright + uv + npm).
> Updates dann inkrementell.

## Onboarding pro Tool

### hermes-runtime

```bash
# Dashboard im Browser
open https://kirobi.local/hermes/                # Caddy-Route, LAN-only
# oder direkt
open http://127.0.0.1:9119

# Modell auf Ollama umstellen ist bereits via Wrapper-Config Default.
# Default-Modell aus .env (HERMES_DEFAULT_MODEL) — anpassen + neu starten.
```

### openclaw-gateway

```bash
# Token einmalig erzeugen (oder leer lassen für Auto-Generierung)
openssl rand -hex 32                             # in .env als OPENCLAW_GATEWAY_TOKEN

# Erstes Onboarding interaktiv
docker compose --profile external-agents exec openclaw-gateway \
    node dist/index.js onboard

# Channels (Signal, Discord, ...) im Onboarding aktivieren.
# Modelle: Ollama als Default in openclaw.json setzen
#   "model": { "provider": "ollama", "baseUrl": "http://ollama:11434" }
```

### aionui-cockpit

```bash
# Nach Install starten (Headless WebUI über Xvfb)
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
    /usr/bin/AionUi --webui --remote --no-sandbox &

# JWT-Passwort initial setzen
cd /opt/aionui && bun run resetpass

# WebUI
open http://127.0.0.1:25808
```

## Sicherheits-Boundary

- Beide Container hängen am internen `kirobi-net` und reden mit Ollama via Service-DNS.
- Caddy gated `/hermes/*` und `/openclaw/*` durch `@not_edge_private` — Zugriff nur aus RFC1918 oder Tailscale (`100.64.0.0/10`).
- **FAMILY_PRIVATE und SACRED** Pfade werden den Containern **nicht** gemountet.
- Hermes-API-Server bleibt off (Default) — niemals ohne `API_SERVER_KEY` exponieren.
- OpenClaw läuft mit `cap_drop: [NET_RAW, NET_ADMIN]` und `no-new-privileges`.

## Skill-/Aufgaben-Verteilung

- **hermes-runtime** ist die zentrale Reasoning-Frontend-Adresse für KEYBRODI sobald Phase 4 startet (`skill_hub_request` → `hermes-runtime`).
- **openclaw-gateway** ist die zweite Schiene neben `telegram` für ausgehende Messaging-Bridges (`messaging_bridge` → `openclaw-gateway`).
- **aionui-cockpit** ist Sven's Operator-Werkzeug — keine programmatische Routing-Adresse.

Routing-Tabelle siehe ADR §"Routing-Tabelle".

## Updates

```bash
# Submodules auf neueste Refs ziehen
make external-update-submodules

# Image-Rebuild
docker compose --profile external-agents build

# AionUi-Upgrade
bash infra/scripts/install-aionui.sh --upgrade
```

## Troubleshooting

| Symptom | Ursache | Fix |
|---|---|---|
| `make external-up` failt mit Submodule-Fehler | Submodules nicht initialisiert | `git submodule update --init --recursive` |
| Hermes-Build OOM | uv-Sync braucht RAM | Build mit `DOCKER_BUILDKIT=1` und ggf. mehr RAM/Swap |
| Caddy `/hermes/*` → 403 | Quelle nicht in `private_ranges` oder Tailscale | Vom LAN/Tailscale aus zugreifen, oder `private_ranges` in Caddyfile erweitern |
| OpenClaw-Token-Mismatch | `.env` lehrt, aber Volume hat alten Token | Volume löschen oder Token aus `openclaw_config_data` lesen |
| AionUi `dpkg -i` Fehler | Fehlende Deps | `sudo apt install -f -y` |
| Qdrant `/qdrant/*` → 403 | Caddy-Gate, nicht aus LAN | Gleicher Fix wie Hermes |
| Flowise startet, Caddy-Proxy 502 | Flowise braucht 30–60s | Healthcheck in Compose wartet jetzt — `docker compose ps flowise` zeigt `healthy` |

## Roll-Back

```bash
make external-down
docker volume rm opendisruption_hermes_data \
                 opendisruption_openclaw_config_data \
                 opendisruption_openclaw_workspace_data
git submodule deinit -f external/hermes-agent external/openclaw
bash infra/scripts/install-aionui.sh --uninstall
```
