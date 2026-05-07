---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kidi/context_db

SQLite-basierter Kontext-Speicher fuer den kidi MCP-Server. Persistiert Key-Value-Paare mit Zonen-Klassifizierung und optionalem TTL unter `~/.kirobi/context.db`.

## Zweck

Agenten und Tools koennen ueber diesen Layer Kontext-Informationen sitzungsuebergreifend ablegen und abrufen. Der Zugriff ist durch den Zonen-Guard abgesichert: Nur `PUBLIC` und `WORKSPACE` duerfen ueber den MCP-Server geschrieben werden. `FAMILY_PRIVATE` und `SACRED` sind blockiert, solange `KIROBI_EGRESS_ALLOWED` nicht explizit gesetzt ist.

## Wichtige Dateien

| Datei | Beschreibung |
|-------|-------------|
| `store.py` | CRUD-Operationen auf der SQLite-Datenbank; verwaltet Schema-Initialisierung, TTL-Pruefung und Ablauf-Bereinigung |
| `zone_guard.py` | Zonen-Hierarchie und Zugriffskontrolle; blockiert unerlaubte Lese-/Schreibzugriffe und Egress-Verletzungen |
| `client.py` | Programmatischer Client fuer den Context-Store; wird von `agents/_base/agent.py` genutzt |
| `keys.py` | Hilfsfunktionen zur Key-Normalisierung und -Validierung |
| `errors.py` | Eigene Ausnahmen: `ZoneViolation`, `EgressViolation`, `SacredApprovalMissing`, `ContextDBError` |
| `__init__.py` | Paket-Exporte |

## Zonen-Hierarchie

```
PUBLIC(0) < WORKSPACE(1) < FAMILY_PRIVATE(2) < SACRED(3)
QUARANTINE(99) — immer isoliert
```

## Datenbankschema

```sql
context_entries (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    zone       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at REAL          -- Unix-Timestamp; NULL = kein Ablauf
)
```
