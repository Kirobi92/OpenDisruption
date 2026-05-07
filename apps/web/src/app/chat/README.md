---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# apps/web/src/app/chat

Next.js-Route fuer die Chat-Oberflaeche der Family PWA. Stellt die Hauptseite bereit, ueber die Nutzer Konversationen mit dem Kirobi-Backend fuehren koennen.

## Zweck

Diese Route implementiert den vollstaendigen Chat-Client: Authentifizierung, Konversationsverwaltung, Nachrichtenversand und -empfang sowie Markdown-Rendering der Antworten. Die Kommunikation erfolgt ueber die REST-API des `api`-Service (Port 8003).

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `page.tsx` | Einzige Route-Komponente; enthaelt den gesamten Chat-UI-State, Konversationsliste, Nachrichtenverlauf und Eingabeformular |

## Datenmodell (lokal)

- `User` — Angemeldeter Nutzer mit `id`, `username`, `display_name`, `role`
- `Message` — Einzelne Nachricht mit `role` (user/assistant/system), `content`, `created_at`
- `Conversation` — Konversations-Metadaten mit `zone`-Klassifizierung

## Abhaengigkeiten

- `axios` — HTTP-Kommunikation mit dem API-Service
- `react-markdown` — Markdown-Rendering der Assistenten-Antworten
- `@heroicons/react` — Icon-Set fuer UI-Elemente
- Next.js App Router (`'use client'`)

## Hinweise

- Die Komponente prueft beim Laden den Auth-Status; bei fehlendem Token erfolgt Redirect zur Login-Seite.
- Zone-Klassifizierung der Konversationen wird vom Backend gesetzt und im UI angezeigt.
