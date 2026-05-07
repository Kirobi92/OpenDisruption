---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kirobi-embeddings

Erzeugt Vektor-Embeddings via Ollama (nomic-embed-text) für die RAG-Pipeline.

## Zweck

Zentraler Embedding-Service für alle Agenten. Kapselt die Ollama-Embedding-API
und bietet eine einheitliche Schnittstelle für den Ingest- und Retrieval-Service.

## API-Endpoints

| Method | Path | Beschreibung | Auth |
|--------|------|--------------|------|
| GET | /health | Health-Check + Ollama-Status | Nein |
| POST | /embed | Batch-Embeddings (bis 100 Texte) | Nein |
| POST | /embed/single | Einzelnes Embedding | Nein |

## Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `OLLAMA_HOST` | `http://ollama:11434` | Ollama-URL |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding-Modell (768-dim) |
| `EMBEDDINGS_SERVICE_PORT` | `8006` | Service-Port |

## Starten

```bash
docker compose up embeddings
```

## Abhängigkeiten

- `ollama` — LLM-Inferenz (nomic-embed-text muss geladen sein)
