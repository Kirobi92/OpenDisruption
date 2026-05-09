# apps – Frontend-Anwendungen und Clients

**Zone:** WORKSPACE | **Verantwortlich:** kirobi-coder

## Zweck
Alle Frontend-Anwendungen und UI-Surfaces des Kirobi-Stacks.

## Anwendungen

| Verzeichnis | App | Status |
|-------------|-----|--------|
| `web/` | Family PWA (Next.js 15) | **Unterstützt** – zentrale Web-Oberfläche, produktionswürdig |
| `dashboard/` | Admin-/Ops-Dashboard (Next.js 15) | **Unterstützt** – Admin-/Status-Oberfläche |
| `voice/` | Voice-Interface (Next.js 15) | **Unterstützt** – Sprach-UI für `voice-processing` |
| `desktop/` | Tauri + React Desktop-Client | **Scaffold** – Grundgerüst, nicht supportet |
| `mobile/` | Expo / React Native Mobile-Client | **Scaffold** – Grundgerüst, nicht supportet |
| `installer/` | Installer-App | **Docs-only** – kein fertiger UI-Wizard im Repo |

## Kanonische Einstiege

- Familie: `apps/web/` hinter Caddy (`kirobi.local`) oder direkt auf Port `3002`
- Admin/Ops: `apps/dashboard/` auf Port `3003`
- Sprache: `apps/voice/` auf Port `3004`

Open WebUI (`3000`) und Flowise (`3001`) gehören zur Compose-Stack-Oberfläche, aber nicht zu `apps/`.
