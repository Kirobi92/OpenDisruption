# 01 — Current State Inventory

**Datum:** 2026-05-26 · **Quellen:** drei parallele READ-ONLY-Explore-Agents + direkte Reads · **Evidenz:** Pfad/Datei
**Hinweis:** Da kein Service in dieser Audit-Sitzung gestartet wurde, ist `RUNNING_VERIFIED` ausschließlich erlaubt, wenn ein vorhandenes Log/Audit den Lauf bestätigt — markiert als `RUNNING_VERIFIED (per Log)`.

## A) Services & Runtime-Komponenten

| Komponente | Pfad | Aktuelle Domäne | Zweck | Stack | Startmechanismus | Port | Datenabhängigkeiten | Zustand | Business-Wert | Family-Wert | Risiko | Evidenz |
|---|---|---|---|---|---|---|---|---|---:|---:|---|---|
| Caddy Reverse Proxy | `services/caddy/` | SHARED | HTTP-Eintritt zu allen Services | Docker (caddy:2-alpine) | `docker compose up` | 0.0.0.0:80 | volumes caddy_data/_config | CONFIGURED_NOT_RUNNING_VERIFIED | 3 | 3 | HIGH (kein HTTPS, Routen ohne Auth) | `services/caddy/docker-compose.yml`, `Caddyfile` |
| Hermes Agent | `hermes-agent/` | SHARED→KIROBI | Multi-Channel-Agent (Telegram/Chat) | Docker + systemd | `docker compose up` + `hermes-gateway-*.service` | 127.0.0.1:9119 (dashboard) | `~/.hermes` | RUNNING_VERIFIED (per Log) | 2 | 4 | HIGH (groß ~7.2 GB, .venv im Tree) | `hermes-agent/docker-compose.yml`, `MASTERPLAN-24H-AUTONOMIE.md` |
| Hermes Gateway Sven | `Orchestrierung-und-Agenten/01-Hermes/systemd/hermes-gateway-sven.service` | KIROBI | Telegram-Bot Sven | systemd user | `systemctl --user start` | n/a (out) | hermes-agent | RUNNING_VERIFIED (per Log) | 1 | 4 | MED (Bot-Token in .env) | unit file |
| Hermes Gateway Samira | `…/hermes-gateway-samira.service` | KIROBI | Telegram-Bot Samira | systemd user | dito | n/a | hermes-agent | RUNNING_VERIFIED (per Log) | 0 | 4 | MED | unit file |
| Kirobi PWA | `kirobi-pwa/` + `kirobi-pwa.service` | KIROBI | SvelteKit Self-Portal | Node systemd | systemctl | **0.0.0.0:4300** | data dir | CONFIGURED_NOT_RUNNING_VERIFIED | 0 | 4 | HIGH (0.0.0.0 statt 127.0.0.1) | `kirobi-pwa.service:14` |
| Qdrant (Systembetrieb) | `Systembetrieb-und-Indizes/qdrant/compose.yaml` | SHARED | Vektorindex | Docker (qdrant:v1.17.1) | docker compose | 127.0.0.1:6333/6334 | `./storage`, `./snapshots` | RUNNING_VERIFIED (per Log) | 4 | 3 | LOW (lokal gebunden, healthcheck vorhanden) | compose.yaml:17–21 |
| Qdrant DUPLICATE | `services/qdrant/` (10 GB Daten) | SHARED | Alter Vektorindex-Datenpfad ohne Compose | Daten-Verzeichnis | manuell | n/a | – | LEGACY / DUPLICATE | 0 | 0 | HIGH (10 GB Runtime im Repo) | dir listing |
| Ollama | (host, kein Compose im v0.1) | SHARED | lokales LLM | Host-Service | manuell/systemd extern | 11434 | Modelle in `/Datenspeicher/OpenDisruption_KI_Modelle` | RUNNING_VERIFIED (per Log) | 4 | 4 | MED (nicht versioniert) | MASTERPLAN, AGENTS.md |
| Hindsight | `services/hindsight/` (138 MB Runtime) | LABS | Session-Archiv-Suche | Compose **fehlt** | unbekannt | 5300/5301 (Caddy-Route) | `pg0-data/` | EXPERIMENTAL / BROKEN | 1 | 1 | MED (kein Compose, Runtime im Repo) | Caddyfile, dir listing |
| Flowise | `services/flowise/` (832 KB) | LABS | LLM-Flow-Builder | Compose **fehlt** | unbekannt | 3001 | `./data`, `./logs`, `database.sqlite` | EXPERIMENTAL | 1 | 1 | HIGH (SQLite im Repo) | Caddyfile route /flowise→3001 |
| Open WebUI | `services/open-webui/` (6.9 GB) | LABS | LLM Web UI | Compose **fehlt** | unbekannt | 3000 | `data/webui.db`, `.webui_secret_key` | EXPERIMENTAL | 1 | 2 | HIGH (6.9 GB im Repo + SQLite + Secret-Datei) | dir |
| Mission Control | `services/mission-control/` | LABS | Ops-Dashboard | Compose **fehlt** | unbekannt | 4100 | `./data` | EXPERIMENTAL | 1 | 1 | MED | Caddyfile /mission→4100 |
| InvenTree | (extern? Docker-Network) | LUKI?/LABS | ERP-Lagerverwaltung | Docker (extern) | unbekannt im v0.1 | 4999 | Postgres extern | RUNNING_VERIFIED (per Log) | 3 | 0 | HIGH (Token in Logs) | MASTERPLAN, AGENT-ACTIVITY-LOG |
| ComfyUI | (host) | LABS | Bildgenerierung | Host-venv in Benutzer-Ordner | manuell | 8188 | `Benutzer-Ordner/Sven/local-ai/ComfyUI` | RUNNING_VERIFIED (per Log) | 1 | 2 | MED (Modelle/Outputs im Tree) | MASTERPLAN |
| Homebox | `services/inventory/homebox/` | LABS | Haushalt-Inventar | Docker | docker compose | 0.0.0.0:8201 | volume | CONFIGURED_NOT_RUNNING_VERIFIED | 0 | 2 | MED (0.0.0.0) | compose:7–18 |
| Part-DB | `services/inventory/partdb/` | LABS | Elektronik-Bauteil-DB | Docker + MySQL | docker compose | 0.0.0.0:8200 | partdb_db | CONFIGURED_NOT_RUNNING_VERIFIED | 0 | 1 | HIGH (Default-Admin-PW im Compose) | compose:19 |
| Webshop WordPress | `services/webshop/` + `/data/webshop-wordpress` | LABS | WP-Shop 3D-Druck-Bar | Docker | docker compose | **0.0.0.0:9001, 0.0.0.0:3307** | 174 MB host-mount Live-DB | RUNNING_VERIFIED (per Log) | 1 | 0 | CRITICAL (DB-Volume `root:root`, MySQL-Port offen, PW in Compose) | webshop/docker-compose.yml |
| Webshop MySQL | dito | LABS | Backend-DB | Docker MySQL 8 | dito | 0.0.0.0:3307 | `/data/webshop-mysql` (101 MB) | RUNNING_VERIFIED (per Log) | 1 | 0 | CRITICAL | dito |
| Static Website | `services/website/` | LABS | Landing | Docker nginx | docker compose | 0.0.0.0:8080 | RO index.html | CONFIGURED_NOT_RUNNING_VERIFIED | 0 | 0 | LOW | compose |
| 3D-Druck-Bar Site | `services/3d-druck-bar-website/` | LABS | Statusseite | GitHub Pages CI | extern | 8081 (Caddy) | extern Repo | EXPERIMENTAL | 1 | 0 | LOW | deploy.yml |
| 3D-Druck-Pipeline | `services/3d-druck-pipeline/` | LABS | Druck-Job-Orchestrierung | unbekannt | unbekannt | – | – | UNKNOWN | 1 | 0 | CRITICAL (Klartext-Secrets in .env) | `.env` |
| IONOS Integration | `services/ionos-integration/` | LABS | Hosting-API | unbekannt | unbekannt | – | – | UNKNOWN | 1 | 0 | LOW | .env.template |
| Status Reporter | `services/status-reporter/` | SHARED | System-Health | unbekannt | unbekannt | – | – | UNKNOWN | 1 | 1 | LOW | dir |

### Compose-Inventar (vollständig)

| Datei | Stack | Port-Binding | Healthcheck | Restart |
|---|---|---|---|---|
| `services/caddy/docker-compose.yml` | caddy:2-alpine | 0.0.0.0:80 | – | unless-stopped |
| `services/inventory/homebox/docker-compose.yml` | homebox:latest | 0.0.0.0:8201 | – | unless-stopped |
| `services/inventory/partdb/docker-compose.yml` | part-db1 + mysql:8 | 0.0.0.0:8200 | mysqladmin | unless-stopped |
| `services/website/docker-compose.yml` | nginx:alpine | 0.0.0.0:8080 | – | always |
| `services/webshop/docker-compose.yml` | wordpress + mysql:8 | 0.0.0.0:9001 + 3307 | – | unless-stopped |
| `hermes-agent/docker-compose.yml` | hermes-agent:latest | 127.0.0.1:9119 | – | unless-stopped |
| `Systembetrieb-und-Indizes/qdrant/compose.yaml` | qdrant:v1.17.1 | 127.0.0.1:6333/6334 | tcp 6333 | unless-stopped |

### Systemd-Units (im Tree)

| Pfad | Type | Beschreibung |
|---|---|---|
| `kirobi-pwa/kirobi-pwa.service` | service | SvelteKit (PORT 4300, HOST 0.0.0.0) |
| `Orchestrierung-und-Agenten/01-Hermes/systemd/hermes-gateway-sven.service` | service | Hermes Gateway Sven |
| `…/hermes-gateway-samira.service` | service | Hermes Gateway Samira |
| `hermes-agent/plugins/kanban/systemd/hermes-kanban-dispatcher.service` | service | DEPRECATED |
| `Benutzer-Ordner/Sven/agent/hermes-runtime/home/.config/systemd/user/obsidian-graph-export.{service,timer}` | s+t | Obsidian Export |

## B) Daten-/Benutzerbereich (Klassifikation)

| Pfad | Inhalt | Datentyp | Zone | Ziel-Domäne | Vermischungs-Risiko | Größe | Evidenz |
|---|---|---|---|---|---|---:|---|
| `Benutzer-Ordner/Sven/` | persönlich + hermes-runtime + local-ai (ComfyUI .venv) + Smartphone-Extrakt + TikTok-Scripts + Projekte | gemischt | FAMILY_PRIVATE + BUSINESS | KIROBI + Teile→SHARED/LUKI | **HIGH** | 24 GB | dir |
| `Benutzer-Ordner/Samira/` | rezepte, meetings, chatgpt-export, KI-Gedächtnis | Personenbezug | FAMILY_PRIVATE | KIROBI | HIGH (privat im Geschäfts-Repo) | 532 MB | dir |
| `Benutzer-Ordner/Sineo/` | persönliche Wissensbasis | Personenbezug | FAMILY_PRIVATE/SINEO_SAFE | KIROBI | HIGH | 314 MB | dir |
| `Benutzer-Ordner/LUKI/` | LUKI-Agent-Profile/Config | Config | BUSINESS | **LUKI_BUSINESS** | MED (in Family-Ordner) | 202 MB | dir |
| `Benutzer-Ordner/Shared/` | Familie/Austausch/Projekte-Shared | shared | FAMILY_SHARED | KIROBI | LOW | 32 KB | dir |
| `Benutzer-Ordner/_Muster-Benutzerstruktur/` | Template | Vorlage | BUSINESS | ARCHIVE/LABS | LOW | 1.1 MB | dir |
| `Geteilte-Wissensbasis/` | Canon, Familie, Business, Bewusstsein | Wissen | gemischt | KIROBI + LUKI (split nötig) | LOW | 140 KB | dir |
| `Orchestrierung-und-Agenten/` | Hermes-Automation, Agent-Profile, Audit | Config + Logs | BUSINESS | SHARED | MED | 316 KB | dir |
| `Integrationen-und-Importe/` | Import-Mappings, Provider-Katalog | Config | BUSINESS | SHARED | LOW | 68 KB | dir |
| `Systemkonfiguration/` | Umgebungen/Secrets-Hinweise, Compose, Schemas | Config + Secrets | BUSINESS/INFRA | SHARED | **HIGH** | 64 KB | dir |
| `Unternehmensstruktur/` | 13 Abteilungen (Hardware/Web3/Software/3D-Druck/Lebenscoach …) | Business-Doku | BUSINESS | LUKI/LABS | LOW | 184 KB | dir |
| `Nutzeisen Prozessanalyse/` | IST-Prozesse, eNVenta-Hilfe, WhatsApp-Konzept | LUKI-Quellmaterial | BUSINESS | **LUKI_BUSINESS** | MED (dupliziert Root-PDF) | 76 MB | dir |
| `Backups-und-Exporte/` | Audit-Berichte, Telegram-Berichte | Backup + Reports | BUSINESS | ARCHIVE | MED | 84 KB | dir |
| `Systembetrieb-und-Indizes/` | Retrieval-Indizes, Logs, Healthchecks, Qdrant | **Runtime!** | INFRA | **NEVER GIT** → /Datenspeicher/OpenDisruption-Data/ | HIGH | 3.1 MB | dir |
| `data/webshop-mysql/` | Live MySQL Volume `root:root` | Runtime DB | INFRA/BUSINESS | **NEVER GIT** | CRITICAL | 101 MB | ls -la |
| `data/webshop-wordpress/` | Live WP Volume | Runtime DB | INFRA/BUSINESS | **NEVER GIT** | CRITICAL | 174 MB | ls -la |
| `node_modules/` | npm deps | Runtime | – | DELETE | MED | 29 MB | dir |
| `.opencode/` | OpenCode-Agent-Runtime | Runtime | – | DELETE_LATER | MED | 58 MB | dir |
| `.hermes/`, `.omo/` | Agent-Pläne/Drafts | Cache | – | NEVER GIT | LOW | <100 KB | dir |
| `.backup.env` | Restic-Secret | Secret | – | NEVER GIT | CRITICAL | 114 B | ls |
| `geplante_ERP-eNVenta-verwendung_Nutzeisen.pdf` (Root) | ERP-Plan (dupliziert in `Nutzeisen Prozessanalyse/`) | Dokument | BUSINESS | LUKI | LOW | 4.2 MB | ls |
| `opendisruption-data-dash.html` | Standalone HTML-Dashboard | Doku | – | ARCHIVE | LOW | 20 KB | ls |
| `hermes-agent/` (gesamt) | Source + vermutlich .venv + caches | Code+Runtime | INFRA | SHARED (Source) + auslagern Runtime | HIGH | 7.2 GB | du |
| `services/qdrant/` | alter Vektorindex | Runtime | INFRA | NEVER GIT | HIGH | 10 GB | du |
| `services/open-webui/` | UI Runtime + secret_key | Runtime+Secret | INFRA | NEVER GIT | HIGH | 6.9 GB | du |
| `services/hindsight/` | Agent Runtime | Runtime | INFRA | NEVER GIT | MED | 138 MB | du |
| Root MD-Dokus (`README`, `SYSTEM_MAP`, `AGENTS`, `KIROBI_OS_AUDIT`, `MASTERPLAN`, `AGENT-ACTIVITY-LOG`) | Audits/Doku | Doku (z.T. mit Secrets!) | – | OPENDISRUPTION_ROOT | HIGH (Secret-Leak) | <100 KB | siehe Phase 2 |

### Top-Level-Größenübersicht (du -sh)

| Bereich | Größe | Status |
|---|---:|---|
| `Benutzer-Ordner/` | 25 GB | mischt privat/business/runtime |
| `services/` | 17 GB | enthält Runtime-Volumes |
| `hermes-agent/` | 7.2 GB | Source + Runtime vermischt |
| `data/` | 275 MB | Live-DBs im Repo (CRITICAL) |
| `Nutzeisen Prozessanalyse/` | 76 MB | LUKI-Quellmaterial |
| `.opencode/` | 58 MB | Runtime |
| `node_modules/` | 29 MB | Runtime |
| `Systembetrieb-und-Indizes/` | 3.1 MB | Runtime-Logs |
| Rest (KB-Bereich) | <1 MB | OK |
| **Summe** | **~50 GB** | – |

## C) Parallel-Tree (summarisch)

`/Datenspeicher/home-migration/OpenDisruption/` (per Symlink `/home/sven/OpenDisruption`): eigene Struktur mit `agents/`, `apps/`, `kidi/`, **`kirobi-core/` UND `kirobi_core/` (Duplikat!)**, `quarantine/`, `external/`, `frontend/`, `infra/`, `experiences/`, `docker-compose.override.yml`. **Klassifikation: Migrationsartefakt — ARCHIVE-Kandidat nach Inhaltsvergleich (Phase B).** VERIFIED via ls.

## D) Drift-Befunde gegen Alt-Audits

| Quelle | Aussage | Realität | Drift |
|---|---|---|---|
| README.md | „Hermes ist Orchestrator" | Bestätigt durch `hermes-agent/` + systemd-Units | KEIN Drift |
| README.md Projektstruktur | listet `Orchestrierung-und-Agenten/01-Hermes/Hermes-Optimierte-OpenDisruption/` | Bestätigt | KEIN Drift |
| README.md | LUKI nicht erwähnt | Aber `Benutzer-Ordner/LUKI/` und `Nutzeisen Prozessanalyse/` existieren | **DRIFT** — LUKI emergent, nicht dokumentiert |
| MASTERPLAN | „Service X aktiv" | Compose teils fehlend (Hindsight, Flowise, Open-WebUI, Mission-Control) | **DRIFT** — Services laufen ohne versionierte Compose |
| AGENTS.md | „Qdrant bindet 127.0.0.1" | Bestätigt für `Systembetrieb-und-Indizes/qdrant/compose.yaml` | KEIN Drift |
| AGENTS.md | Caddy „exposes local/LAN/Tailscale" | Bestätigt | KEIN Drift, aber Sicherheitsfrage offen |
| AGENT-ACTIVITY-LOG | enthält Klartext-Credentials | Bestätigt mehrfach | **CRITICAL Drift** — Sicherheitsregel verletzt |

## E) Zentrale Befunde

1. **Keine saubere Produkttrennung:** KIROBI/LUKI/Labs leben unsortiert in `services/`, `Benutzer-Ordner/`, Wurzel-PDFs.
2. **Runtime-Daten im Repo:** `services/qdrant` (10 GB), `services/open-webui` (6.9 GB), `data/` (275 MB Live-DBs), `node_modules` — verletzen das Zielprinzip „Runtime außerhalb Repo".
3. **Compose-Lücken:** 4 wichtige Services (Hindsight, Flowise, Open-WebUI, Mission-Control) haben keine Compose-Definition — nicht reproduzierbar.
4. **Secret-Leaks dokumentiert:** mindestens 11 Klartext-Secrets gefunden (Details Phase 2).
5. **Doppelter Codebase-Tree:** `/Datenspeicher/home-migration/OpenDisruption` existiert parallel und enthält selbst Duplikate (`kirobi-core` + `kirobi_core`).
6. **LUKI-Material vorhanden:** `Nutzeisen Prozessanalyse/` (76 MB) + `Benutzer-Ordner/LUKI/` (202 MB) + Wurzel-PDF — Grundlage für LUKI-MVP existiert, ist aber nicht produktisiert.
7. **Netzwerk-Exposition:** Caddy auf `0.0.0.0:80`, mehrere Compose-Stacks auf `0.0.0.0:*`, Kirobi-PWA auf `0.0.0.0:4300` — kein konsequentes Loopback-/Tailscale-Modell.
