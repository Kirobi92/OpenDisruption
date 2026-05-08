---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-08
reviewed_by: pending
version: "1.0"
---

# 30-Tage-Plan: Persönlicher Speicher und autonomes Lernen

Dieser Plan bringt OpenDisruption schrittweise in einen sicheren Zustand, in
dem Svens Dateien, Dokumente, Bilder, Eingaben und Erkenntnisse lokal erfasst,
klassifiziert, auffindbar und lernbar werden.

Das Ziel ist nicht „alles sofort lesen“, sondern: **alles sicher erfassbar
machen** — mit klaren Gates, lokaler Verarbeitung und vollständiger
Nachvollziehbarkeit.

## Zielbild nach 30 Tagen

- Neue Dateien starten kontrolliert in einem Manifest oder in QUARANTINE.
- PUBLIC/WORKSPACE-Inhalte können autonom vorbereitet und indexiert werden.
- FAMILY_PRIVATE und SACRED haben explizite Review-/Freigabeprozesse.
- Qdrant und Postgres sind abgeleitete, rebuildbare Indizes.
- Sven sieht offene Entscheidungen, Fortschritt und Risiken im Dashboard.
- Agenten können nur auf freigegebene Zonen zugreifen.
- Erkenntnisse werden vorgeschlagen, aber erst nach Review kanonisiert.

## Woche 1: Sicherheitsfundament und Inventar

### Tag 1: Architektur-Freeze

- Personal-Memory-Datenfluss finalisieren.
- Stop-Regeln bestätigen.
- Entscheiden, welche WORKSPACE/PUBLIC-Pfade autonom verarbeitet werden dürfen.

Output:

- `docs/autonomous-knowledge-cycle.md`
- offene Gate-Fragen für Sven

### Tag 2: Metadata-only Manifest stabilisieren

- `ingest-manifest` als sicheren Einstieg nutzen.
- Keine Inhalte lesen.
- PUBLIC/WORKSPACE stage, alles andere block.

Validierung:

```bash
python3 -m kirobi_core ingest-manifest --repo-root . README.md docs kirobi_core
python3 -m pytest tests/unit -q
```

### Tag 3: Manifest erweitern

- SHA256 ergänzen, aber nur nach Policy.
- MIME-Type ergänzen.
- optionale JSONL-Ausgabe vorbereiten.
- Speicherort planen: `metadata/personal-memory/manifests/`.

### Tag 4: Review-Gate-Modell

- Entscheidungen definieren: approve, reject, keep_quarantined, mark_sacred.
- Audit-Felder definieren.
- Keine Inhalte promoten.

### Tag 5: Risk Flags

- Heuristiken definieren:
  - untrusted source
  - unknown suffix
  - possible secret
  - possible family/private
  - large archive
  - outside repo

### Tag 6: Report-Format

- Scan-Report mit Counts nach Zone, Action, Risiko.
- Keine sensiblen Inhalte im Report.

### Tag 7: Wochenreview

- Prüfen: Welche Pfade sind sicher automatisierbar?
- Prüfen: Welche Gates fehlen?
- Nächste P0-Implementierung wählen.

## Woche 2: Sichere Ingestion-Pipeline

### Tag 8: Postgres-State entwerfen

- Tabellenentwurf:
  - `personal_files`
  - `ingest_jobs`
  - `approvals`
  - `extracted_chunks`
  - `memory_index_entries`
  - `insight_jobs`
  - `audit_events`

### Tag 9: API-Contract entwerfen

- `/ingest/scan`
- `/ingest/files`
- `/approvals/pending`
- `/approvals/{id}/decision`
- `/memory/search`
- `/insights/jobs`

### Tag 10: QUARANTINE-Prozess

- QUARANTINE nur als Metadatenquelle.
- Keine Embeddings.
- Keine Prompts.
- Keine automatische Promotion.

### Tag 11: Safe Extraction PUBLIC/WORKSPACE

- Markdown/Text zuerst.
- PDF/DOCX später mit lokalen Parsern.
- Provenance immer speichern.

### Tag 12: Chunking-Strategie

- deterministische Chunk-IDs
- Content-Hash
- Quellenreferenz
- Zone pro Chunk

### Tag 13: Qdrant-Collection-Matrix

- Collection-Namen vereinheitlichen.
- Keine gemischten Zonen.
- SACRED standardmäßig nicht indexieren.

### Tag 14: Wochenreview

- End-to-End Dry Run nur mit PUBLIC/WORKSPACE-Testdaten.
- Blockierte Fälle prüfen.

## Woche 3: Suche, Retrieval und Erkenntnisse

### Tag 15: Lokale Embeddings

- Ollama/nomic-embed-text prüfen.
- `/store`-Roundtrip testen.
- Collection-Naming angleichen.

### Tag 16: Retrieval Zone Enforcement

- SACRED immer 403.
- QUARANTINE nicht trusted.
- FAMILY_PRIVATE nur mit Freigabe.

### Tag 17: Suche für WORKSPACE/PUBLIC

- Quellen, Zone, Confidence anzeigen.
- Keine stille Vermischung von Zonen.

### Tag 18: Insight-Modell

- Unterschied dokumentieren:
  - Raw Source
  - Extract
  - Chunk
  - Summary
  - Insight
  - Canon Candidate
  - Experience

### Tag 19: Erste Insight-Jobs

- Themencluster
- Duplikate
- offene Fragen
- Projektkandidaten

### Tag 20: Review für Insights

- Insights sind Vorschläge.
- Promotion nur mit Sven-Freigabe.

### Tag 21: Wochenreview

- Qualität der Treffer bewerten.
- Falsche Klassifikationen als Learnings erfassen.

## Woche 4: UX, Alltag und autonomer Betrieb

### Tag 22: Ingestion-UI

- Route `/ingest`.
- Sicherheitsversprechen sichtbar machen.
- Fortschritt anzeigen.

### Tag 23: Review-UI

- Route `/review`.
- Zone bestätigen/ändern.
- QUARANTINE behalten.
- SACRED markieren.

### Tag 24: Storage-Status

- Route `/storage/status`.
- Counts nach Zone.
- offene Reviews.
- fehlgeschlagene Jobs.

### Tag 25: Agent Access Matrix

- Sichtbar machen, welcher Agent welche Zone sehen darf.
- Zugriff zeitlich begrenzen.
- Audit anzeigen.

### Tag 26: Lernen aus User Inputs

- Nur abstrahierte Learnings speichern.
- Keine sensiblen Gesprächsdetails ohne Freigabe.
- Korrekturen als Systemwissen markieren.

### Tag 27: Autonomer Tageszyklus

- Morgens manifestieren.
- Mittags sichere Verarbeitung.
- Nachmittags Insights.
- Abends Review-Report.

### Tag 28: Backup und Rebuild

- Prüfen, welche Daten rebuildbar sind.
- Approvals und Audit als nicht-rebuildbar sichern.
- Backup-Dry-Run dokumentieren.

### Tag 29: Vollständiger Dry Run

- Nur PUBLIC/WORKSPACE-Testdaten.
- scan → manifest → classify → extract → index → search → insight → report.

### Tag 30: Sven-Review

Sven entscheidet:

- Welche Ordner dürfen autonom vorbereitet werden?
- Welche Inhalte bleiben immer manuell?
- Welche Reports sind täglich/wöchentlich wertvoll?
- Welche Agenten erhalten welche Speicherzonen?

## Priorisierte autonome Aufgaben

### P0

1. Manifest um Hash/MIME/JSONL-Ausgabe erweitern.
2. Collection-Naming zwischen Init, Embeddings und Retrieval vereinheitlichen.
3. QUARANTINE/FAMILY/SACRED in Ingest/Embeddings fail-closed setzen.
4. Security-Tests für Zone-Leaks ergänzen.

### P1

1. Review-Queue API entwerfen.
2. PUBLIC/WORKSPACE Text-Extraction implementieren.
3. Retrieval-Roundtrip mit lokalen Testdaten absichern.
4. `/ingest`, `/review`, `/storage/status` als PWA-Flows bauen.

### P2

1. OCR/STT lokal und gated ergänzen.
2. Insight-Jobs produktiv machen.
3. Agent Access Matrix integrieren.
4. Wochenreport automatisieren.

## Metriken

- Dateien im Manifest
- staged vs. blocked
- offene Reviews
- erfolgreiche Extraktionen
- indexierte Chunks
- blockierte Sicherheitsfälle
- neue Insights
- akzeptierte/verwarfene Canon-Kandidaten

## Definition von Erfolg

OpenDisruption ist erfolgreich, wenn Sven sagen kann:

> „Ich kann alles in mein System legen — und trotzdem weiß ich jederzeit, was
> sicher ist, was wartet, was privat bleibt und was meine Agenten wirklich sehen
> dürfen.“
