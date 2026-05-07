---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# apps/web/src/app/health

Next.js Route Handler für den Health-Check-Endpoint der PWA.
Liefert einen einfachen `200 OK` Status zurück — wird von Caddy, Docker Healthchecks und dem Monitoring genutzt.

## Wichtige Dateien

- `route.ts` — Next.js App Router Route Handler: `GET /health` → `{ status: "ok" }`
