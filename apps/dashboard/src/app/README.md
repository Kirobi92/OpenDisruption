---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# apps/dashboard/src/app

Next.js 15 App-Router-Wurzel des Kirobi Admin-Dashboards.

## Dateien

- `layout.tsx` — Root-Layout: setzt HTML-Sprache (`de`), Inter-Font, Dark-Mode-Klasse und Seiten-Metadaten (`noindex, nofollow`)
- `page.tsx` — Einzige Route (`/`): vollständiges Admin-Dashboard als Client Component
- `globals.css` — Globale TailwindCSS-Stile, Utility-Klassen (`card`, `nav-item`, `status-dot-*`)

## Was das Dashboard zeigt

Das Dashboard hat vier Bereiche, zwischen denen per Sidebar navigiert wird:

| Bereich | Inhalt |
|---------|--------|
| **Services** | Health-Check aller internen Services mit Latenz und Status-Badge |
| **Analytics** | Events heute, aktive User, Konversationen, Nachrichten, Zonen-Nutzung |
| **Benutzer** | Statische Übersicht der Familie Darusi (Sven, Samira, Sineo) |
| **System** | Ollama-Status, PostgreSQL, Qdrant, geladene Modelle mit Größe |

## Verhalten

- Auto-Refresh alle 30 Sekunden via `setInterval`
- Alle Service-Checks laufen parallel (`Promise.all`)
- Fehler bei einzelnen Checks degradieren den Status, brechen aber nicht die gesamte Ansicht
- Kein Login — das Dashboard ist nur über Caddy im LAN erreichbar (`dashboard.local`)

## Abhängigkeiten

- `axios` für HTTP-Requests gegen `/api/*`-Endpunkte (Caddy-Proxy)
- `@heroicons/react` für Icons
- TailwindCSS mit Custom-Farbe `kirobi`
