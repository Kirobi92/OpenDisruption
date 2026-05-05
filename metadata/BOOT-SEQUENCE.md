# Boot-Sequenz: Kirobi / Disruptive OS

**Version:** 1.0 | **Zone:** WORKSPACE

---

## Übersicht Boot-Sequenz

Die Boot-Sequenz beschreibt die Reihenfolge, in der Kirobi / Disruptive OS beim Start initialisiert wird.

```
Phase 0: Infrastruktur
  └─> PostgreSQL starten & health check
  └─> Qdrant starten & health check
  └─> Ollama starten & Modelle laden
  └─> Flowise starten & verbinden
  └─> Open WebUI starten & verbinden

Phase 1: Core-Initialisierung
  └─> kirobi-core Kontext laden
  └─> Policies laden
  └─> Event-Log öffnen
  └─> Agent-Registry einlesen

Phase 2: Agenten-Start
  └─> kirobi-observer (zuerst – Monitoring)
  └─> hermes-extractor (Inbox-Check)
  └─> Weitere Agenten nach Bedarf

Phase 3: Zustand-Wiederherstellung
  └─> Offene Tasks prüfen
  └─> Fehler aus letzter Session analysieren
  └─> Health-Report generieren
```

---

## Detaillierte Schritte

### Phase 0: Infrastruktur (automatisch via Docker)

```bash
# 1. PostgreSQL
docker compose up -d postgres
# Wait: pg_isready check

# 2. Qdrant
docker compose up -d qdrant
# Wait: GET /health → 200

# 3. Ollama
docker compose up -d ollama
# Wait: GET /api/tags → 200

# 4. Flowise
docker compose up -d flowise
# Wait: GET /api/v1/flows → 200

# 5. Open WebUI
docker compose up -d open-webui
# Wait: GET / → 200
```

### Phase 1: Core-Initialisierung

kirobi-core führt beim Start folgende Aktionen durch:

1. **Kontext laden** aus `kirobi-core/core-context.md`
2. **Policies laden** aus `kirobi-core/core-policies.md`
3. **Event-Log öffnen** `kirobi-core/core-events.log`
4. **Agent-Registry einlesen** aus `metadata/AGENTREGISTRY.md`
5. **System-Config laden** aus `metadata/SYSTEMCONFIG.md`
6. **Letztes Sitzungs-Summary** aus PostgreSQL laden

### Phase 2: Systemzustand

Bei jedem Start analysiert kirobi-observer:
- Offene Inbox-Einträge in `sources/inbox/`
- Fehler in `quarantine/failed-ingests/`
- Offene Reviews in `quarantine/review-needed/`
- System-Health der Docker-Services
- Modell-Verfügbarkeit in Ollama

---

## Fehlerbehandlung beim Boot

| Fehler | Auswirkung | Fallback |
|--------|-----------|---------|
| PostgreSQL down | Kein Zustandsspeicher | Lokale JSON-Datei |
| Qdrant down | Kein Vektorabruf | Nur Keyword-Suche |
| Ollama down | Keine LLM-Inferenz | Cloud-API Fallback (nur PUBLIC) |
| Flowise down | Keine Workflows | Direkte API-Calls |
| Open WebUI down | Kein Chat-Interface | CLI-Interface |

---

## Shutdown-Sequenz

Beim geordneten Shutdown:
1. Laufende Aufgaben abschließen oder pausieren
2. Event-Log mit "SHUTDOWN"-Eintrag schließen
3. Qdrant-Flush erzwingen
4. PostgreSQL-Checkpoint
5. Docker-Services stoppen: WebUI → Flowise → Agenten → Qdrant → PostgreSQL → Ollama
