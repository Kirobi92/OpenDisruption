---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# integrations/connectors – Connector-Definitionen

Dieses Verzeichnis enthält Connector-Definitionen für die Anbindung externer und interner Systeme an das Kirobi-Ökosystem. Connectors kapseln die technischen Details einer Verbindung (Auth, Endpoints, Datenformat) und werden von Flowise-Flows, n8n-Workflows oder dem Hermes-Extraktor referenziert.

## Zweck

Connectors abstrahieren den Zugriff auf externe Dienste. Statt Verbindungsdetails in jedem Flow zu wiederholen, wird ein Connector einmalig definiert und wiederverwendet. Das reduziert Fehlerquellen und erleichtert Credential-Rotation.

## Konvention

Jede Connector-Datei folgt dem Schema:

```
[dienst]-connector.yaml   # z. B. m365-outlook-connector.yaml
[dienst]-connector.json   # alternativ als JSON für Flowise-Import
```

## Typische Felder

```yaml
name: m365-outlook
type: oauth2
base_url: https://graph.microsoft.com/v1.0
auth:
  flow: authorization_code
  token_url: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
scopes:
  - Mail.Read
  - Mail.Send
zone: WORKSPACE
```

## Sicherheitshinweis

Connector-Dateien dürfen **keine echten Credentials** enthalten. Zugangsdaten gehören ausschließlich in `.env` oder ein Secret-Management-System. Connector-Dateien referenzieren Umgebungsvariablen (`${M365_CLIENT_ID}`).

## Verwandte Verzeichnisse

- `integrations/config/` – Allgemeine Integrations-Konfigurationen
- `integrations/flows/` – Flowise-Flows, die Connectors nutzen
- `integrations/APIS/` – API-Dokumentation und OpenAPI-Specs
