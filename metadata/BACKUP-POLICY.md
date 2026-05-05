# Backup-Policy: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Backup-Strategie: 3-2-1 Regel

- **3** Kopien der Daten
- **2** verschiedene Speichermedien
- **1** offsite Backup (verschlüsselt)

## Backup-Zeitplan

| Was | Häufigkeit | Aufbewahrung | Ziel |
|-----|-----------|-------------|------|
| Qdrant Snapshot | Täglich 02:00 | 30 Tage | /mnt/backup/qdrant/ |
| PostgreSQL Dump | Täglich 02:30 | 30 Tage | /mnt/backup/postgres/ |
| canon/ | Täglich 03:00 | 90 Tage | /mnt/backup/canon/ |
| experiences/ | Täglich 03:30 | 90 Tage | /mnt/backup/experiences/ |
| sacred/ | Wöchentlich | 1 Jahr (verschlüsselt) | Externes Medium |
| Vollständig | Monatlich | 1 Jahr | Externes Medium |

## Verschlüsselung

- Alle Backups werden mit AES-256 verschlüsselt
- SACRED-Backups haben eigenen Schlüssel (offline gespeichert)
- Backup-Schlüssel niemals im Repository

## Recovery-Tests

- Monatliche Recovery-Tests für kritische Backups
- Dokumentation in `analytics/system-health.md`
- Recovery-Zeit-Ziel (RTO): 4 Stunden
- Recovery-Punkt-Ziel (RPO): 24 Stunden
