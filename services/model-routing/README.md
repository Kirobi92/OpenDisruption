---
zone: WORKSPACE
created_by: keycodi
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# kirobi-model-routing

Intelligente Modell-Selektion basierend auf Task-Typ und GPU-Verfügbarkeit.

## Zweck

Zentraler Router für Ollama-Modelle. Wählt automatisch das optimale Modell
basierend auf Task-Typ, Verfügbarkeit und Performance-Anforderungen.

## API-Endpoints

| Method | Path | Beschreibung | Auth |
|--------|------|--------------|------|
| GET | /health | Health-Check + verfügbare Modelle | Nein |
| POST | /route | Modell für Task-Typ wählen | Nein |
| GET | /models | Alle Ollama-Modelle | Nein |
| GET | /routing-table | Routing-Konfiguration | Nein |

## Task-Typen

| Task-Typ | Primär-Modell | Fallback |
|----------|---------------|---------|
| chat | llama3.1:8b | llama3.2:3b |
| code | qwen2.5-coder:7b | llama3.1:8b |
| reasoning | deepseek-r1:7b | llama3.1:8b |
| embedding | nomic-embed-text | nomic-embed-text |
| vision | llava:7b | llama3.2-vision:11b |
| supervisor | llama3.1:8b | llama3.2:3b |

## Abhängigkeiten

- `ollama` — LLM-Inferenz
