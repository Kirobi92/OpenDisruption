---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/retrieval – Retrieval-Tests

Tests für die Qdrant-basierte Vektorsuche und den Retrieval-Augmented-Generation (RAG)-Stack. Sie prüfen Suchqualität, Zonen-Isolation in Qdrant-Collections und die korrekte Rückgabe relevanter Dokumente.

## Zweck

Retrieval ist das Gedächtnis von Kirobi. Retrieval-Tests stellen sicher, dass:
- Suchanfragen die richtigen Dokumente zurückgeben
- Zonen-Grenzen in Qdrant-Collections eingehalten werden (kein FAMILY_PRIVATE in WORKSPACE-Suche)
- Embedding-Qualität ausreichend ist
- Latenz und Trefferquote akzeptabel bleiben

## Testbereiche

| Bereich | Was wird geprüft |
|---------|-----------------|
| Zonen-Isolation | FAMILY_PRIVATE-Dokumente erscheinen nicht in WORKSPACE-Suchen |
| Relevanz | Top-K-Ergebnisse sind semantisch passend |
| Embedding-Konsistenz | Gleiche Texte erzeugen gleiche Vektoren |
| Collection-Struktur | Collections folgen dem Schema `kirobi_{zone}_{type}` |
| Fehlerbehandlung | Qdrant-Ausfall wird graceful behandelt |

## Ausführen

```bash
# Alle Retrieval-Tests (benötigt laufenden Qdrant-Service)
python -m pytest tests/retrieval/ -v

# Nur Unit-Tests für Retrieval-Service (gemockt, offline)
python -m pytest tests/unit/test_retrieval_service.py -v

# Mit Qdrant-Service starten
docker compose up qdrant -d
python -m pytest tests/retrieval/ -v
```

## Voraussetzungen

Retrieval-Tests benötigen einen laufenden Qdrant-Service. Für CI-Umgebungen werden Qdrant-Calls gemockt (siehe `tests/unit/test_retrieval_service.py`).

## Verwandte Tests

- `tests/unit/test_retrieval_service.py` – Gemockte Unit-Tests
- `tests/unit/test_embeddings_service.py` – Embedding-Service-Tests
- `tests/unit/test_zones.py` – Zonen-Klassifizierung
