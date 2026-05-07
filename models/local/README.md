---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# models/local

Übersicht und Konfiguration der lokal über Ollama betriebenen Sprachmodelle.

## Zweck

Alle LLM-Inferenz im OpenDisruption-System läuft lokal über Ollama — kein Modell-Traffic geht an externe Cloud-APIs. Dieser Ordner dokumentiert, welche Modelle installiert sind, wofür sie eingesetzt werden und welche Ressourcen sie benötigen.

## Modell-Auswahl nach Aufgabe

| Aufgabe | Empfohlenes Modell | Profil |
|---------|-------------------|--------|
| Chat / Konversation | `llama3.1:8b` | CPU + GPU |
| Komplexe Analyse | `llama3.1:70b` | GPU (≥ 24 GB VRAM) |
| Code-Generierung | `qwen2.5-coder:7b` | CPU + GPU |
| Embedding (WORKSPACE) | `bge-m3` (1024d) | CPU |
| Embedding (PUBLIC) | `nomic-embed-text` (768d) | CPU |
| Vision / Bild-Analyse | `llava:7b` | CPU + GPU |

## Fallback-Verhalten

Der `model-routing`-Service wählt automatisch ein kleineres Modell, wenn das bevorzugte Modell nicht verfügbar ist (z. B. GPU-Memory-Limit). Fallback-Reihenfolge: `70b → 8b → 3b`.

## Modelle verwalten

```bash
# Installiertes Modell prüfen
docker exec kirobi-ollama ollama list

# Modell laden
docker exec kirobi-ollama ollama pull llama3.1:8b

# Modell entfernen
docker exec kirobi-ollama ollama rm llama3.1:70b
```

## Verwandte Services

- `services/model-routing/` — Routing-Logik und Fallback-Strategie
- Ollama läuft als Compose-Service auf Port `11434` (intern)
