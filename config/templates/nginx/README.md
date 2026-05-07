---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# config/templates/nginx/

Nginx-Konfigurationsvorlage als Alternative zu Caddy. Wird eingesetzt, wenn Unternehmensrichtlinien oder bestehende Infrastruktur Nginx vorschreiben.

## Dateien

- `nginx.kirobi.conf` — Nginx-Konfiguration mit HTTP-zu-HTTPS-Redirect, TLS-Terminierung (via certbot) und Reverse-Proxy-Routing

## Verwendung

1. `REPLACE_HOSTNAME` durch den tatsächlichen Hostnamen ersetzen
2. Datei nach `/etc/nginx/conf.d/kirobi.conf` kopieren
3. TLS-Zertifikate via certbot bereitstellen (Pfad: `/etc/letsencrypt/live/REPLACE_HOSTNAME/`)

## Routing-Übersicht

| Pfad | Upstream | Beschreibung |
|------|----------|--------------|
| `/auth/` | `127.0.0.1:8002` | Authentifizierungs-Service |
| `/api/` | `127.0.0.1:8003` | Backend-API |
| `/` | `127.0.0.1:3002` | Family PWA (Next.js) |

## Hinweis

Der primäre Reverse Proxy im Standard-Stack ist Caddy (`config/templates/caddy/`). Diese Nginx-Vorlage deckt nur die drei Kern-Upstreams ab; Open WebUI und Flowise sind nicht enthalten. Änderungen an Proxy-Konfigurationen sind sicherheitssensitiv und erfordern menschliche Freigabe.
