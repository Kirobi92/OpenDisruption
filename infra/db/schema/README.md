---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Datenbankschema

Dieser Ordner enthält die SQL-Migrationsdateien für die PostgreSQL-Datenbank
des Kirobi-Systems. Migrationen werden nummeriert und sequenziell ausgeführt.

## Konvention

Dateinamen folgen dem Muster `NNN_beschreibung.sql` — die Nummer bestimmt die
Ausführungsreihenfolge. Migrationen sind **nicht rückwärtskompatibel** zu löschen;
stattdessen neue Migrationsdatei anlegen.

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `001_family_profiles.sql` | Initiales Schema für Familienprofile |

## Hinweis

Schemaänderungen erfordern menschliche Freigabe, da sie Produktionsdaten betreffen können.
