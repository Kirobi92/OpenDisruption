---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# integrations/mcp

Model Context Protocol (MCP) — Server-Definitionen und Konfigurationen für die Kirobi-Agenten.

## Zweck

MCP ermöglicht es Agenten, strukturiert auf externe Tools und Datenquellen zuzugreifen. Dieser Ordner enthält MCP-Server-Konfigurationen, die von Agenten (z. B. über OpenCode oder direkt) genutzt werden.

## Was ist MCP?

MCP (Model Context Protocol) ist ein offenes Protokoll, das LLMs standardisierten Zugriff auf Tools, Ressourcen und Prompts gibt. Ein MCP-Server stellt Funktionen bereit (z. B. Datei-Lesen, DB-Abfragen), die das Modell aufrufen kann.

## Konventionen

- Dateiname: `{service}-mcp-server.json` oder `mcp-config.json`
- Jeder MCP-Server muss Zone-konform sein: keine SACRED/FAMILY_PRIVATE-Daten an externe Server
- Lokale MCP-Server (Dateisystem, Postgres) sind bevorzugt gegenüber Cloud-MCP-Servern

## Sicherheitshinweis

MCP-Server mit Schreibzugriff (Dateisystem, Datenbank) erfordern explizite Genehmigung durch Sven, bevor sie aktiviert werden. Lese-only-Server für PUBLIC/WORKSPACE-Daten können ohne Genehmigung konfiguriert werden.

## Verwandte Konfiguration

- `.opencode/` — OpenCode-Konfiguration mit MCP-Server-Einbindung
- `opencode.json` — Projekt-Root-Konfiguration
