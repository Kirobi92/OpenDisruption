---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kirobi-ingest

Hermes-Extractor: Verarbeitet `sources/inbox/` → `extracts/` → Qdrant.

## Zweck

Automatisierte Ingestion-Pipeline für neue Dokumente. Liest Dateien aus dem
Inbox-Ordner, chunked den Text, erzeugt Embeddings und speichert sie in Qdrant.

## API-Endpoints

| Method | Path | Beschreibung | Auth |
|--------|------|--------------|------|
| GET | /health | Health-Check | Nein |
| POST | /ingest | Datei ingestieren | Nein |
| GET | /inbox | Inbox-Inhalt auflisten | Nein |

## Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `EMBEDDINGS_SERVICE_URL` | `http://embeddings:8006` | Embeddings-Service |
| `QDRANT_HOST` | `qdrant` | Qdrant-Host |
| `KIROBI_INBOX_PATH` | `/repo/sources/inbox` | Inbox-Pfad |
| `KIROBI_EXTRACTS_PATH` | `/repo/extracts/workspace` | Extracts-Pfad |
| `INGEST_SERVICE_PORT` | `8007` | Service-Port |

## Unterstützte Dateitypen (Phase 1)

- `.txt`, `.md`, `.json`, `.yaml`, `.yml`

## Abhängigkeiten

- `embeddings` — Embedding-Erzeugung
- `qdrant` — Vektor-Speicher
