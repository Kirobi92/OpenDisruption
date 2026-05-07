---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# Komponenten (`apps/web/src/components`)

Wiederverwendbare React-Komponenten der Kirobi Family PWA.

## Enthaltene Komponenten

### `AppNav.tsx`

Globale Navigation der PWA — passt sich automatisch an die Bildschirmgröße an.

**Verhalten:**
- **Desktop (≥ md)**: Horizontale Top-Bar mit Logo und Navigationslinks
- **Mobil (< md)**: Fixierte Bottom-Bar mit Icon + Label pro Eintrag
- **Login-Seite (`/`)**: Navigation wird vollständig ausgeblendet — kein Nav ohne eingeloggten Nutzer

**Navigationspunkte:**

| Route | Label | Icon |
|-------|-------|------|
| `/chat` | Chat | `ChatBubbleLeftRightIcon` |
| `/search` | Suche | `MagnifyingGlassIcon` |
| `/upload` | Upload | `CloudArrowUpIcon` |
| `/settings` | Einstellungen | `Cog6ToothIcon` |

**Aktiver Zustand**: Ein Link gilt als aktiv, wenn `pathname.startsWith(href)` — dadurch bleiben auch Unter-Routen korrekt hervorgehoben.

**Einbindung**: `AppNav` wird im Root-Layout (`apps/web/src/app/layout.tsx`) eingebunden und erscheint damit auf allen Seiten außer `/`.

## Konventionen für neue Komponenten

- Dateiname in `PascalCase`, Suffix `.tsx`
- `'use client'` nur wenn Browser-APIs oder React-Hooks benötigt werden
- Keine direkten API-Calls in Komponenten — Datenabruf gehört in die jeweilige `page.tsx`
- Tailwind-Klassen bevorzugen; keine separaten CSS-Module
