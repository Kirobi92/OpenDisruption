---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Desktop App — Quellcode (`apps/desktop/src`)

React-Komponenten der Kirobi Desktop-App (Tauri + React 18 + Vite).

## Enthaltene Dateien

| Datei | Zweck |
|-------|-------|
| `main.tsx` | Vite-Einstiegspunkt — rendert `<App />` in `#root` |
| `index.css` | Globale Styles: Layout, Sidebar, Karten, Chat-Bubbles, Einstellungen |
| `App.tsx` | Root-Komponente mit Sidebar-Navigation und allen Unter-Ansichten |

## Architektur

`App.tsx` verwaltet den aktiven View-Zustand und rendert eine von drei Ansichten:

```
App
├── Sidebar (Navigation: Dashboard | Chat | Einstellungen)
├── Dashboard   — API-Health-Check gegen VITE_API_URL/health
├── Chat        — Einfaches Chat-Interface gegen VITE_API_URL/chat
└── Einstellungen — API-URL-Konfiguration, Tray-Hinweis, Versionsinformation
```

## Konfiguration

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `VITE_API_URL` | `http://kirobi.local/api` | Basis-URL des Kirobi-API-Service — via Caddy geroutet |

Die Variable wird in `.env` im Projekt-Root gesetzt (nicht in `apps/desktop/.env`).

## Status

🚧 **Scaffold** — Die App ist funktionsfähig als Grundgerüst, aber noch nicht feature-vollständig:
- Kein JWT-Auth-Flow (kein Login-Screen)
- Kein Datei-Upload, keine Wissenssuche
- System-Tray-Verhalten ist in `src-tauri/tauri.conf.json` konfiguriert (noch nicht implementiert)

## Starten (Entwicklung)

```bash
cd apps/desktop
npm install
npm run dev        # Vite Dev-Server
npm run tauri dev  # Tauri + Vite (benötigt Rust-Toolchain)
```
