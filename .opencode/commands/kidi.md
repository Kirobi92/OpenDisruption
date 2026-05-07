---
description: KIDI Context-DB Operationen — put, get, query, ping. Verwaltet den Agenten-Kontext-Speicher.
agent: kirobi-coder
subtask: true
---

# KIDI Context-DB: $ARGUMENTS

KIDI ist der Redis-basierte Kontext-Speicher für das Multi-Agenten-System.

**Status prüfen:**
!`python3 -m pytest tests/unit -k kidi -v 2>&1`

**Verfügbare Operationen (nach Argument):**

Falls Argument "ping": Prüfe Redis-Verbindung
Falls Argument "test": Führe KIDI-Tests aus
Falls Argument "status": Zeige KIDI-Konfiguration

**KIDI-Modul-Übersicht:**
```
kidi/
├── context_db/
│   ├── client.py      ← ContextDB-Klasse (Redis-basiert)
│   ├── zone_guard.py  ← Zone-Enforcement
│   ├── keys.py        ← Key-Schema: ZONE:agent:category:uuid
│   └── errors.py      ← Typed Exceptions
└── __init__.py
```

**Key-Schema:**
```
WORKSPACE:keycodi:task:uuid4
WORKSPACE:kirobi-coder:result:uuid4
PUBLIC:research-crew:summary:uuid4
```

**Zone-Regeln:**
- SACRED: Niemals schreiben/lesen ohne explizite Freigabe
- FAMILY_PRIVATE: Nur lokal (KIROBI_EGRESS_ALLOWED=false)
- WORKSPACE: Standard für Agenten-Kommunikation
- PUBLIC: Für geteilte, nicht-sensitive Daten

Analysiere den aktuellen KIDI-Status und berichte.
