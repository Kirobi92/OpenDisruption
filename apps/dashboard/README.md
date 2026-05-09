---
zone: WORKSPACE
created_by: kirobi-frontend
created_at: 2026-05-07
reviewed_by: pending
version: 1.0
---

# Kirobi Dashboard (`apps/dashboard/`)

Admin-Dashboard für das OpenDisruption-Ökosystem — eigenständige Next.js 15 App auf Port **3003**.

## Features

- **Operator-Control-Panel** — lokaler Supervisor-Status, Human-Gates, Dead-Letter und letzte Kontroll-Events
- **Produkt-Aktivität** — jüngste Logins, Uploads und Gesprächsbewegungen für MVP-Operatoren
- **Services-Panel** — Health-Check aller 7 Backend-Services mit Latenz-Anzeige und Fortschrittsbalken
- **Analytics-Panel** — Events heute, aktive User, Zonen-Nutzung (WORKSPACE, FAMILY_PRIVATE, PUBLIC, SACRED)
- **Benutzer-Panel** — Übersicht der Familie Darusi (Sven, Samira, Sineo)
- **System-Panel** — Ollama-Modelle, PostgreSQL- und Qdrant-Status
- **Auto-Refresh** alle 30 Sekunden
- **Dunkles Theme** (bg-gray-900) mit TailwindCSS

## Stack

| Paket | Version |
|-------|---------|
| Next.js | 15.5.15 |
| React | 18.3.1 |
| TypeScript | 5.6.3 (strict) |
| TailwindCSS | 3.4.14 |
| axios | 1.15.2 |
| @heroicons/react | 2.1.5 |

## Entwicklung

```bash
cd apps/dashboard
npm install
npm run dev      # http://localhost:3003
```

## Build

```bash
npm run build
npm run start
```

## Lint

```bash
npm run lint
```

## Architektur

Alle API-Calls gehen über Caddy (`/api/*`) — nie direkt zu den Services.
Das Dashboard ist **nicht** für den öffentlichen Zugriff gedacht (`robots: noindex`).

## Ports

| Service | Port |
|---------|------|
| Family PWA (`apps/web`) | 3000 |
| Dashboard (`apps/dashboard`) | 3003 |
