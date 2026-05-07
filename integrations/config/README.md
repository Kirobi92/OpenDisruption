---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# integrations/config – Integrations-Konfigurationen

Konfigurationsdateien für alle Integrationen des Kirobi-Ökosystems: Verbindungsparameter, Feature-Flags, Timeout-Werte und Service-spezifische Einstellungen für Flowise, Qdrant, Ollama, n8n, Langfuse und weitere.

## Zweck

Integrations-Konfigurationen trennen die technischen Verbindungsdetails von der Geschäftslogik. Statt Konfiguration in Code oder Flows zu vergraben, werden sie hier zentral verwaltet und können ohne Code-Änderungen angepasst werden.

## Datei-Konvention

```
[dienst]-config.yaml    # Haupt-Konfiguration
[dienst]-config.json    # Alternativ für JSON-basierte Tools
[umgebung]/             # Umgebungsspezifische Overrides (dev/, prod/)
```

## Typische Konfigurationsfelder

```yaml
# Beispiel: qdrant-config.yaml
service: qdrant
host: ${QDRANT_HOST:-localhost}
port: ${QDRANT_PORT:-6333}
collections:
  workspace: kirobi_workspace_docs
  family: kirobi_family_docs        # FAMILY_PRIVATE
timeout_seconds: 30
retry_attempts: 3
```

## Sicherheitshinweis

- Keine Secrets in Konfigurationsdateien – nur Umgebungsvariablen-Referenzen (`${VAR}`)
- Konfigurationen mit Zonen-Angabe versehen, wenn sie sensible Dienste betreffen
- Änderungen an produktiven Konfigurationen erfordern menschliche Genehmigung

## Verwandte Verzeichnisse

- `integrations/connectors/` – Connector-Definitionen (Auth, Endpoints)
- `integrations/flows/` – Flowise-Flows, die Konfigurationen nutzen
- `.env.example` – Umgebungsvariablen-Template
- `infra/` – Infrastruktur-Konfigurationen (Docker, Caddy)
