---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# archive/snapshots – System-Snapshots

Zeitgestempelte Snapshots des Kirobi-Systems: Datenbank-Dumps, Konfigurationsstände und Zustandsbilder zu bestimmten Zeitpunkten. Dienen als Rollback-Basis und historische Referenz.

## Zweck

Snapshots sichern den Systemzustand vor größeren Änderungen (Migrationen, Upgrades, Refactorings). Sie ermöglichen eine schnelle Wiederherstellung ohne vollständiges Backup-Restore.

## Inhalt eines Snapshots

Ein Snapshot-Verzeichnis enthält typischerweise:

```
snapshots/
  2026-05-07_pre-migration/
    postgres-dump.sql.gz      # Postgres-Datenbankstand
    qdrant-export.json.gz     # Qdrant-Vektoren (optional)
    docker-compose.yml        # Aktiver Compose-Stand
    .env.redacted             # Env-Variablen ohne Secrets
    SNAPSHOT-INFO.md          # Beschreibung, Grund, Ersteller
```

## Erstellen eines Snapshots

```bash
# Vor einer Migration oder einem größeren Update
bash infra/scripts/backup.sh --dry-run   # Erst trocken laufen lassen
bash infra/scripts/backup.sh             # Dann ausführen
```

## Wichtige Hinweise

- Snapshots können **Secrets und Familiendaten** enthalten – niemals teilen oder committen
- Generierte Tarballs gehören **nicht** ins Git-Repository
- `.gitkeep` hält das Verzeichnis im Repository, ohne Inhalte zu versionieren
- Alte Snapshots regelmäßig bereinigen (Speicherplatz)

## Verwandte Verzeichnisse

- `infra/scripts/backup.sh` – Backup-Skript
- `archive/` – Übergeordnetes Archiv-Verzeichnis
- `.kirobi/install.json` – Installationsstatus für Referenz
