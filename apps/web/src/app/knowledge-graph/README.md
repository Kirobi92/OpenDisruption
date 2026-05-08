---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# KIDI Knowledge Graph Demo

Knappe Dokumentation zur lokalen Demo-Route für einen synthetischen KIDI Knowledge Graph MVP.

## Zweck

Die Route zeigt, wie sich ein integraler Wissensraum visuell anfühlen kann, bevor echte Graphdaten angebunden werden. Sie dient als sichere UI-Probe für Navigation, Tiefenwirkung, Zonen-Badges und spätere API-Verträge.

## Route

- Pfad: `/knowledge-graph`
- Datei: `page.tsx`
- Laufzeit: Next.js Client Component (`'use client'`)
- Datenquelle: statische Demo-Arrays im Client, keine Requests

## Datenmodell und Komponentenüberblick

- `GraphNode`: synthetischer Knoten mit `id`, `label`, integraler `stage`, `zone`, 3D-Projektionswerten, `radius` und Kurzbeschreibung.
- `GraphEdge`: einfache Verbindung zwischen zwei Knoten mit `strength` für die visuelle Liniengewichtung.
- `STAGE_COLORS`: Farbsystem für integrale Entwicklungsstufen von `infrared` bis `turquoise`.
- `DEMO_NODES` / `DEMO_EDGES`: ausschließlich kuratierte PUBLIC/WORKSPACE-Beispieldaten.
- `findNode()`: schützt die Demo vor inkonsistenten Kantenreferenzen.
- `projectionStyle()`: übersetzt synthetische Raumwerte in CSS-Position, Tiefe, Glow und Blur.
- `KnowledgeGraphPage`: rendert Header, SVG-Kanten, CSS-Knoten, Legende, Sicherheitskasten und Link zum Stack-Status.

## Sicherheitsgrenzen

- Keine FAMILY_PRIVATE- oder SACRED-Daten.
- Keine echten privaten Graphdaten.
- Keine externen APIs oder Cloud-Dienste.
- Kein RAG-, Qdrant- oder Datenbankzugriff im Client.
- Späterer Live-Zugriff darf nur über zonengeprüfte `/api/*`-Endpunkte erfolgen.

## Nächster Ausbau

- API-Contract für zonengeprüfte Graph-Abfragen definieren.
- Filter nach Zone, Stage und Knotentyp ergänzen.
- Detailpanel für ausgewählte Knoten hinzufügen.
- Layout-Engine oder serverseitig vorberechnete Koordinaten prüfen.
- Accessibility für Tastatur-Navigation und reduzierte Bewegung weiter ausbauen.
