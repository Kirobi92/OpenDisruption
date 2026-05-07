---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# archive/exports

Archivierte Exporte aus dem OpenDisruption-System — z. B. Daten-Dumps, generierte Reports oder einmalige Ausgaben, die nicht mehr aktiv genutzt werden.

## Zweck

Dateien landen hier, wenn ein Export-Vorgang abgeschlossen ist und das Ergebnis zur Nachvollziehbarkeit aufbewahrt werden soll, aber nicht mehr in den aktiven Workflow gehört.

## Konventionen

- Dateien werden **nicht gelöscht**, sondern bleiben als Audit-Trail erhalten
- Neue Exporte werden mit Datum im Dateinamen abgelegt: `YYYY-MM-DD_beschreibung.ext`
- Kein aktiver Code liest aus diesem Verzeichnis

## Bekannte Einschränkungen

Derzeit leer (`.gitkeep`). Wird bei Bedarf befüllt.
