---
zone: WORKSPACE
type: canon-master
document: security-master
version: 1.0
created_at: 2024-01-01
reviewed_by: kirobi-architect
---

# Canon: Sicherheits-Master-Dokument

## Kern-Sicherheitsprinzipien

### 1. Local-First Security
Alle sensiblen Daten bleiben auf lokalem Hardware. Kein externer Zugriff ohne explizite Freigabe.

### 2. Defense in Depth
Mehrere Sicherheits-Schichten: Zonenmodell, Netzwerk-Isolation, Verschlüsselung, Audit-Logging.

### 3. Principle of Least Privilege
Jeder Agent hat nur die Rechte, die er für seine Aufgabe benötigt.

### 4. Zero-Trust für externe Verbindungen
Alle externen Verbindungen werden als nicht vertrauenswürdig behandelt.

## Bedrohungsmodell

### Bedrohungen

| Bedrohung | Wahrscheinlichkeit | Auswirkung | Maßnahme |
|-----------|-------------------|------------|---------|
| Datenleck durch Cloud-API | Mittel | Hoch | Kein Cloud-API für FAMILY/SACRED |
| Unbefugter Agenten-Zugriff | Niedrig | Hoch | Zonenmodell + HitL |
| Netzwerk-Angriff | Niedrig | Mittel | Docker-Netzwerk-Isolation |
| Schwache Passwörter | Mittel | Mittel | .env mit starken Passwörtern |
| Backup-Kompromittierung | Niedrig | Hoch | Verschlüsselte Backups |

## Netzwerk-Sicherheit

```yaml
# Alle Services laufen im isolierten Docker-Netzwerk
# Nur explizit exponierte Ports sind von außen erreichbar
# Keine direkte Internet-Exponierung der Services
```

## Verschlüsselung

- **In-Transit:** HTTPS für externe Verbindungen, verschlüsselte Tunnel intern
- **At-Rest:** Backup-Verschlüsselung (AES-256)
- **Secrets:** Nur in .env, niemals in Git

## Audit-Logging

Alle Aktionen werden geloggt:
- Agent-Zugriffsversuche
- Zone-Überschreitungen
- Human-in-the-Loop Aktionen
- Service-Start/Stop
