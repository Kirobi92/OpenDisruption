---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/business – Business-Prompts

Prompts für geschäftliche Anwendungsfälle im Kirobi-Ökosystem: Kundenkorrespondenz, Angebotserstellung, Projektplanung, Reporting und Entscheidungsunterstützung.

## Zweck

Business-Prompts unterstützen Sven bei unternehmerischen Aufgaben. Sie sind auf professionelle Kommunikation, strukturiertes Denken und Effizienz ausgelegt – ohne persönliche oder familiäre Daten zu vermischen.

## Namenskonvention

```
[aufgabe]-[kontext]-v[version].md
Beispiele:
  angebot-erstellen-v1.md
  kundenemail-followup-v1.md
  projektplan-strukturieren-v1.md
```

## Kategorien

| Kategorie | Beschreibung |
|-----------|-------------|
| Kommunikation | E-Mails, Angebote, Kundenantworten |
| Planung | Projektstrukturierung, Roadmaps, Priorisierung |
| Analyse | Marktanalyse, Entscheidungsmatrizen, SWOT |
| Reporting | Statusberichte, Zusammenfassungen, Protokolle |
| Strategie | Geschäftsmodell-Entwicklung, Positionierung |

## Zonen-Hinweis

Business-Prompts haben Zone `WORKSPACE`. Sie dürfen keine `FAMILY_PRIVATE`- oder `SACRED`-Daten referenzieren. Kundendaten sind vor Verwendung zu anonymisieren.

## Verwandte Verzeichnisse

- `prompts/enterprise/` – Prompts für Enterprise-Integrationen (M365, eNVenta)
- `prompts/workflows/` – Mehrstufige Workflow-Prompts
- `prompts/system/` – System-Prompts für den enterprise-agent
