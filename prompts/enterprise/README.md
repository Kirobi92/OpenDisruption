---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# prompts/enterprise – Enterprise-Prompts

Prompts für Enterprise-Integrationen: Microsoft 365 (Outlook, Teams, OneDrive), eNVenta ERP und andere Geschäftssystem-Anbindungen. Diese Prompts unterstützen den `enterprise-agent` bei der strukturierten Verarbeitung von Geschäftsdaten.

## Zweck

Enterprise-Prompts überbrücken die Lücke zwischen Kirobi und bestehenden Unternehmens-Tools. Sie definieren, wie der `enterprise-agent` E-Mails analysiert, Kalendereinträge verarbeitet, ERP-Daten interpretiert und Aktionen in M365 auslöst.

## Namenskonvention

```
[system]-[aufgabe]-v[version].md
Beispiele:
  m365-email-analyse-v1.md
  m365-kalender-planung-v1.md
  enventa-auftrag-extraktion-v1.md
  teams-meeting-protokoll-v1.md
```

## Kategorien

| Kategorie | System | Beschreibung |
|-----------|--------|-------------|
| E-Mail | M365 Outlook | Klassifizierung, Zusammenfassung, Antwort-Entwurf |
| Kalender | M365 Calendar | Terminplanung, Konflikt-Erkennung |
| Dokumente | M365 OneDrive | Extraktion, Zusammenfassung |
| Kommunikation | M365 Teams | Meeting-Protokolle, Action-Items |
| ERP | eNVenta | Auftrags-Extraktion, Status-Abfragen |

## Zonen-Hinweis

Enterprise-Prompts haben Zone `WORKSPACE`. Kundendaten und Geschäftsgeheimnisse müssen vor der Verarbeitung anonymisiert werden. M365-Integrationen benötigen explizite Genehmigung für WORKSPACE-Daten.

## Verwandte Verzeichnisse

- `integrations/m365-outlook.md` – Outlook-Integrations-Dokumentation
- `integrations/m365-teams.md` – Teams-Integrations-Dokumentation
- `prompts/business/` – Allgemeine Business-Prompts
- `prompts/workflows/` – Mehrstufige Enterprise-Workflows
