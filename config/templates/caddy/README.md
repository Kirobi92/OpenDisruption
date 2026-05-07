---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# config/templates/caddy/

Caddy-Konfigurationsvorlage für den produktiven Betrieb des OpenDisruption-Stacks. Caddy ist der primäre LAN-seitige Reverse Proxy und TLS-Terminator.

## Dateien

- `Caddyfile.production` — Produktions-Template mit Routing-Regeln für alle Services

## Verwendung

Die Vorlage muss vor dem Einsatz angepasst werden:

1. `REPLACE_HOSTNAME` durch den tatsächlichen Hostnamen ersetzen
2. Datei nach `infra/caddy/Caddyfile` kopieren

## Routing-Übersicht

| Pfad | Ziel | Beschreibung |
|------|------|--------------|
| `/` | `web:3002` | Family PWA (Next.js) |
| `/auth/*` | `auth:8002` | Authentifizierungs-Service |
| `/api/*` | `api:8003` | Backend-API |
| `/chat/*` | `open-webui:8080` | Lokales LLM-Interface |
| `/flows/*` | `flowise:3000` | Workflow-Orchestrierung |

## Hinweis

Caddy ist der einzige Service, der auf LAN/Tailscale hört (`KIROBI_PROXY_BIND_HOST`). Alle Backend-Ports binden auf `127.0.0.1`. Änderungen an dieser Datei sind sicherheitssensitiv und erfordern menschliche Freigabe.
