---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Route: /status

Next.js-Seite für die Stack-Statusübersicht der OpenDisruption-Instanz. Zeigt Live-Probes der Kern-Services und Einstiegslinks zu allen Systemteilen.

## Dateien

- `page.tsx` — Client-Komponente mit automatischer Aktualisierung alle 15 Sekunden

## Funktion

Die Seite führt HTTP-Probes gegen drei Endpunkte durch:

| Service | Probe-URL |
|---------|-----------|
| web | `/health` |
| auth | `/api/auth/health` |
| api | `/api/health` |

Zusätzlich werden alle Systemteile als verlinkbare Kacheln dargestellt (Kirobi PWA, Open WebUI, Flowise, Qdrant Dashboard, API, Auth, Voice).

## Technische Details

- Probe-Timeout: 4 Sekunden pro Service
- Aktualisierungsintervall: 15 Sekunden (via `setInterval`)
- Kein Server-Side-Rendering (`'use client'`)
- Erreichbar unter: `https://<host>/status`

## Hinweis

Die Backend-Ports binden auf `127.0.0.1`. Sicherer Remote-Zugriff auf diese Seite erfordert Tailscale oder LAN-Zugang über Caddy.
