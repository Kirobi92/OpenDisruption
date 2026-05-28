# Network-Hardening Plan — Port-Binding Lockdown

**Status:** PENDING — braucht `sudo` (Sandbox blockt autonomes Ausführen).
**Datum:** 2026-05-28 · **Phase:** C
**Ziel:** Backend-Services aus LAN nehmen, nur via Caddy erreichbar.

---

## Aktueller Zustand (Stand 2026-05-28 07:15)

Caddy gehärtet ✅:
- `127.0.0.1:80` + `100.127.16.62:80` (Tailscale), kein 0.0.0.0 mehr
- 4-User-basicauth auf 19 Routen

**Restliche Backends auf 0.0.0.0** (LAN-exponiert):

| Service | Port | Bind | Caddy-Route | Empfehlung |
|---|---|---|---|---|
| partdb | 8200 | 0.0.0.0 | /partdb (redirect) | bind 127.0.0.1, Caddy proxy statt redirect |
| homebox | 8201 | 0.0.0.0 | /homebox (redirect) | bind 127.0.0.1, Caddy proxy statt redirect |
| 3d-druck-bar-preview | 8081 | 0.0.0.0 | /3dbar | bind docker-bridge IP |
| webshop-wordpress | 9001 | 0.0.0.0 | /wordpress | bind docker-bridge IP |
| opendisruption-website | 8080 | 0.0.0.0 | (kein Caddy-Route, eigener Host) | Caddy-Route hinzufügen, bind 127.0.0.1 |
| webshop-mysql | 3307 | 0.0.0.0 | (kein) | bind 127.0.0.1 (DB-Tools nur lokal) |
| webshop-postgres | 5433 | 0.0.0.0 | (kein) | bind 127.0.0.1 |
| webshop-redis | 6380 | 0.0.0.0 | (kein) | bind 127.0.0.1 |
| inventree-3ddruck | 4999 | 0.0.0.0 | /inventree | bind docker-bridge IP |
| hindsight | 5300/5301 | 0.0.0.0 | /hindsight (5301) | bind 127.0.0.1 + docker-bridge |
| open-webui (3000) | 3000 | 0.0.0.0 | /webui | bind 127.0.0.1 |
| flowise (3001) | 3001 | 0.0.0.0 | /flowise | bind 127.0.0.1 |
| ollama | 11434 | 0.0.0.0 | /ollama | bind 127.0.0.1 |
| mission-control (4100) | 4100 | 0.0.0.0 | /mission | bind 127.0.0.1 |
| paperclip (3100) | 3100 | 127.0.0.1 ✓ | /paperclip | OK |
| qdrant (6333) | 6333 | 127.0.0.1 ✓ | /qdrant | OK |

---

## Lösungs-Ansätze

### A — Docker-Network-Refactor (CLEAN, INVASIV)
Alle Backends an `caddy_net` (extern angelegt) hängen → Caddy reicht via Container-DNS (`reverse_proxy wordpress:80`). Keine Host-Port-Exposition mehr.

**Pro:** Kein LAN-Exposure, sauber, keine Firewall-Wartung.
**Kontra:** Compose-Refactor + Container-Restart für jede App.

### B — Dual-Bind (PRAGMATISCH)
Ports an `127.0.0.1` UND `172.17.0.1` (docker0) binden. Caddy nutzt `host.docker.internal:PORT`.

**Pro:** Minimaler Compose-Patch (nur port-binding).
**Kontra:** docker0-IP ist von allen Containern erreichbar (nicht nur Caddy).

### C — Host-Firewall (UFW)
Backend-Ports im Host-Firewall blockieren außer von Tailscale/Loopback/Docker-Bridges.

**Pro:** Keine Compose-Änderung, sofort wirksam.
**Kontra:** sudo nötig, separates Layer zu warten.

---

## Empfehlung

**Hybrid B+C für Phase C (jetzt), A langfristig (Phase D oder später):**

1. **Sofort (User mit sudo):** UFW-Regel — Allow 80 (Caddy), allow von 100.x/24 (Tailscale-Subnet), allow von 172.16/12 (Docker-Bridges), allow von 127.0.0.1; deny rest auf den Backend-Ports.

2. **Kommende Compose-Patches:** schrittweise Bind auf `127.0.0.1:PORT` + Caddy auf `host.docker.internal:PORT`.

3. **Phase E/F:** vollständiger Docker-Network-Refactor wenn Stacks ohnehin reorganisiert werden.

---

## UFW-Skript (vom User auszuführen)

```bash
#!/bin/bash
# Backend-Port-Lockdown — nur Tailscale + Loopback + Docker-Bridges
set -e

PORTS=(3000 3001 3307 4100 4999 5300 5301 5433 6380 8000 8002 8080 8081 8188 8200 8201 9001 11434)

# UFW Default policies
sudo ufw --force default deny incoming
sudo ufw --force default allow outgoing

# SSH + Caddy ingress
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp

# Backends: nur Tailscale + Docker + Loopback
for p in "${PORTS[@]}"; do
    sudo ufw allow from 100.0.0.0/8 to any port "$p" proto tcp comment 'Tailscale'
    sudo ufw allow from 172.16.0.0/12 to any port "$p" proto tcp comment 'Docker'
    sudo ufw allow from 127.0.0.1 to any port "$p" proto tcp comment 'Loopback'
done

sudo ufw --force enable
sudo ufw status verbose
```

**Verifikation (von einem anderen LAN-Host):**
```bash
nc -zv 192.168.178.10 9001  # WordPress LAN → connection refused/timeout
nc -zv 100.127.16.62 9001    # via Tailscale → connect succeeds (aber Caddy ist die saubere Route)
curl -I http://192.168.178.10/kirobi  # via Caddy LAN → muss noch klappen (Caddy bindet 127.0.0.1 + Tailscale)
```

**Rollback:** `sudo ufw disable` (alle Regeln dropping, alle Ports wieder offen).
