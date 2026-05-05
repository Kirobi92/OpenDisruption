# Event-Taxonomie: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Event-Kategorien

### System-Events (SYS)
| Event | Code | Beschreibung |
|-------|------|-------------|
| System-Start | SYS.BOOT | System wurde gestartet |
| System-Shutdown | SYS.SHUTDOWN | System wurde gestoppt |
| Service-Up | SYS.SVC_UP | Ein Dienst ist verfügbar |
| Service-Down | SYS.SVC_DOWN | Ein Dienst ist nicht verfügbar |
| Health-Check | SYS.HEALTH | Gesundheitsprüfung durchgeführt |
| Backup-Start | SYS.BACKUP_START | Backup begonnen |
| Backup-Ende | SYS.BACKUP_END | Backup abgeschlossen |

### Agenten-Events (AGT)
| Event | Code | Beschreibung |
|-------|------|-------------|
| Task-Gestartet | AGT.TASK_START | Agent beginnt Aufgabe |
| Task-Abgeschlossen | AGT.TASK_END | Agent schließt Aufgabe ab |
| Task-Fehler | AGT.TASK_ERROR | Fehler bei Aufgabe |
| Routing-Entscheidung | AGT.ROUTING | Routing-Entscheidung getroffen |
| Human-in-Loop | AGT.HIL | Menschliche Bestätigung angefordert |
| Zone-Verletzung | AGT.ZONE_VIOLATION | Zone-Policy verletzt (kritisch!) |

### Ingestion-Events (ING)
| Event | Code | Beschreibung |
|-------|------|-------------|
| Datei-Erkannt | ING.FILE_DETECTED | Neue Datei in sources/ |
| Extraktion-Start | ING.EXTRACT_START | Extraktion begonnen |
| Extraktion-Ende | ING.EXTRACT_END | Extraktion abgeschlossen |
| Embedding-Start | ING.EMBED_START | Einbettung begonnen |
| Embedding-Ende | ING.EMBED_END | Einbettung abgeschlossen |
| Quarantäne | ING.QUARANTINE | Datei in Quarantäne verschoben |

### Familien-Events (FAM)
| Event | Code | Beschreibung |
|-------|------|-------------|
| Mediation-Start | FAM.MEDIATION_START | Mediation begonnen |
| Mediation-Ende | FAM.MEDIATION_END | Mediation abgeschlossen |
| Manometer | FAM.MANOMETER | Emotionaler Zustand erfasst |
| Ritual | FAM.RITUAL | Familienritual dokumentiert |

## Event-Log-Format (JSON)

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event_code": "AGT.TASK_END",
  "agent": "hermes-extractor",
  "zone": "WORKSPACE",
  "message": "Datei inbox/dokument.pdf erfolgreich verarbeitet",
  "details": {
    "source": "sources/inbox/dokument.pdf",
    "target": "extracts/workspace/dokument.md",
    "chunks": 15,
    "duration_ms": 3420
  },
  "severity": "INFO"
}
```
