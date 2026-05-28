# Compose-Lücken-Analyse (R-019) — Stand 2026-05-28

**Phase:** C · **Quelle:** `docker ps`, `systemctl --user`, Compose-File-Scan.

---

## Laufende Container ohne nachvollziehbares Compose

| Container | Status | Image | Suche-Ergebnis |
|---|---|---|---|
| `opendisruption-caddy` | Up 8h | caddy:2-alpine | ✅ `services/caddy/docker-compose.yml` |
| `webshop-mysql` | Up 4d | mysql:8.0 | ✅ `services/webshop/docker-compose.yml` |
| `webshop-wordpress` | Up 4d | wordpress:latest | ✅ `services/webshop/docker-compose.yml` |
| `webshop-postgres` | Up 4d | postgres:16-alpine | ✅ `Benutzer-Ordner/Sven/Projekte/Webshop/docker-compose.yml` (gehärtet) |
| `webshop-redis` | Up 4d | redis:7-alpine | ✅ wie oben |
| `partdb` | Up 4d | jbtronics/part-db1 | ✅ `services/inventory/partdb/docker-compose.yml` |
| `partdb-db` | Up 4d | mysql:8.0 | ✅ wie oben |
| `homebox` | Up 4d | ghcr.io/sysadminsmedia/homebox | ✅ `services/inventory/homebox/docker-compose.yml` |
| `3d-druck-bar-preview` | Up 4d | nginx? | ⚠️ Kein Compose gefunden — manuell `docker run` |
| `opendisruption-website` | Up 4d | nginx:alpine | ✅ `services/website/docker-compose.yml` |
| `inventree-3ddruck` | Up 4d | inventree/inventree:stable | ✅ `Benutzer-Ordner/Sven/Projekte/Inventar-System/docker-compose.yml` (gehärtet) |
| `hindsight` | Up 4d | ? | ⚠️ Kein Compose gefunden |

---

## Fehlende Compose-Files (R-019)

### Hindsight Server
- **Container:** `hindsight` (5300/5301)
- **Aktion:** Compose erstellen aus `docker inspect`, Image + Volumes dokumentieren
- **Ziel:** `infra/hindsight/docker-compose.yml`

### 3D-Druck-Bar Preview
- **Container:** `3d-druck-bar-preview` (8081)
- **Aktion:** Wie oben — Compose rekonstruieren aus inspect
- **Ziel:** `labs/3d-druck/docker-compose.preview.yml`

### Mission Control
- **Service:** Caddy-Route `/mission` → 4100 — Container/Service-Quelle unklar
- **Aktion:** Suchen ob systemd-Service oder fehlender Container; ggf. dokumentieren als „nicht aktiv"

### Open-WebUI
- **Service:** Caddy-Route `/webui` → 3000 — kein laufender Container
- **Aktion:** Compose unter `services/open-webui/` existiert (`.venv` zeigt Setup); klären ob Service inactive oder anderer Mechanismus

### Flowise / Paperclip / Ollama / Qdrant / Comfy / Avatar / Shop-Admin
- **Status:** Caddy-Routen existieren, Container-Status pro Service prüfen.

---

## Systemd-User-Services (laufend)

| Unit | Status | Notiz |
|---|---|---|
| `hermes-gateway.service` | active running | Hermes Hauptgateway |
| `hermes-gateway-luki.service` | active running | LUKI-Gateway |
| `cleanup-match-log-backups.timer` | active waiting | OK |

## Systemd-System-Services

| Unit | Status | Notiz |
|---|---|---|
| `kirobi-backup.service` | ✅ fixed in PC.1 (jetzt grün) | täglich 02:30 |
| `kirobi-backup.timer` | active | OK |

---

## Roadmap-Add (Phase D/E)

- **R-037:** Hindsight-Compose rekonstruieren + nach `infra/` migrieren
- **R-038:** 3D-Druck-Bar-Preview-Compose rekonstruieren
- **R-039:** Mission-Control: Service-Quelle klären (systemd? container?) und dokumentieren
- **R-040:** Open-WebUI Compose erstellen + Bind auf 127.0.0.1
