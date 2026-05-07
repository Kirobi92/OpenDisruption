---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# integrations/flows

Flowise-Workflow-Definitionen für das OpenDisruption-System.

## Zweck

Flowise ist das visuelle Workflow-Tool im Kirobi-Stack. Hier werden exportierte Flow-Definitionen (JSON) versioniert, damit Workflows reproduzierbar und nachvollziehbar bleiben.

## Konventionen

- Dateiname: `{zweck}-flow.json` oder `{agent}-flow.json`
- Vor dem Export in Flowise: Flow benennen und Beschreibung setzen
- Flows, die externe APIs aufrufen, müssen Zone-Compliance-geprüft sein (kein FAMILY_PRIVATE / SACRED nach außen)

## Import / Export

```bash
# Flow aus Flowise exportieren (im Flowise-UI):
# Einstellungen → Export → JSON speichern nach integrations/flows/

# Flow importieren:
# Flowise-UI → Import → JSON-Datei auswählen
```

## Sicherheitshinweis

Flows können externe HTTP-Requests auslösen. Vor dem Aktivieren eines neuen Flows prüfen:
- Welche Daten werden gesendet?
- An welchen Endpunkt?
- Ist die Zone der Daten PUBLIC oder WORKSPACE?

Flows mit FAMILY_PRIVATE- oder SACRED-Daten sind **verboten**.

## Verwandte Services

- Flowise läuft als Compose-Service (intern, via Caddy erreichbar)
