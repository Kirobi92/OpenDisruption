# Entscheidungsbaum: Kirobi Routing

**Zone:** WORKSPACE | **Version:** 1.0

---

## Haupt-Entscheidungsbaum

```
Eingehende Anfrage
        │
        ▼
┌───────────────────┐
│ Sicherheitscheck  │
│ Zone bestimmen    │
└────────┬──────────┘
         │
    SACRED? ──── Ja ──→ Human-in-Loop anfordern ──→ Mit Freigabe fortfahren
         │ Nein
         ▼
┌───────────────────┐
│ Anfrage-Typ?      │
└────────┬──────────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
    ▼                                     ▼
Code/Technik                        Familie/Emotional
    │                                     │
    ├── Code schreiben → kirobi-coder     ├── Mediation → samira-heart
    ├── Architektur → kirobi-architect    ├── Sineo → sineo-creator
    ├── DevOps → kirobi-ops               └── Allgemein → kirobi-core
    └── Monitoring → kirobi-observer
    
    Business/Research                  Wissensmgmt/Ingestion
    │                                     │
    ├── Web-Recherche → research-crew     ├── Ingestion → hermes-extractor
    ├── Enterprise → enterprise-agent     └── Suche → kirobi-core + Qdrant
    └── Kreativität → creative-agent
```

---

## Eskalations-Regeln

Wenn ein Agent eine Aufgabe nicht lösen kann:
1. Fehlermeldung an kirobi-core
2. kirobi-core versucht alternatives Routing
3. Wenn kein Routing möglich: Human-in-Loop
4. Event-Log-Eintrag mit Fehlerbeschreibung
