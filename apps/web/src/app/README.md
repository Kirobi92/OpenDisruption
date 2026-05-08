---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Next.js App Router

Haupt-Verzeichnis der Kirobi Family PWA — basiert auf dem Next.js 15 App Router.
Jeder Unterordner entspricht einer Route der Anwendung.

## Struktur

| Pfad | Beschreibung |
|------|-------------|
| `layout.tsx` | Root-Layout: HTML-Shell, globale Provider |
| `page.tsx` | Startseite `/` |
| `globals.css` | Globale CSS-Stile (TailwindCSS-Basis) |
| `chat/` | Chat-Interface für Kirobi-Konversationen |
| `health/` | Health-Check-Endpunkt `/health` |
| `knowledge-graph/` | Synthetische, dependency-freie KIDI-Wissensgraph-Demo (`/knowledge-graph`) |
| `status/` | System-Status-Seite `/status` |

## Konvention

Neue Routen als eigenen Unterordner mit `page.tsx` anlegen.
Gemeinsame UI-Komponenten gehören nach `src/components/`, nicht hierher.
