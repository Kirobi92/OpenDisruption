---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kirobi-retrieval

RAG-Retrieval-Service: Semantische Suche in Qdrant mit Zone-Enforcement.

## Zweck

Einheitliche Suchschnittstelle für alle Agenten. Erzwingt Zone-Isolation:
FAMILY_PRIVATE-Daten sind von PUBLIC/WORKSPACE-Anfragen vollständig getrennt.

## API-Endpoints

| Method | Path | Beschreibung | Auth |
|--------|------|--------------|------|
| GET | /health | Health-Check | Nein |
| POST | /search | Semantische Suche | Nein |
| GET | /collections | Verfügbare Collections | Nein |

## Zone-Enforcement

| Zone | Erlaubte Collections |
|------|---------------------|
| PUBLIC | workspace, canon, research |
| WORKSPACE | workspace, canon, experiences, research, conversations, metadata |
| FAMILY_PRIVATE | family |

## Abhängigkeiten

- `embeddings` — Query-Embedding
- `qdrant` — Vektor-Suche
