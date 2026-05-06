---
zone: WORKSPACE
type: tech-insights
version: 1.0
---

# Technische Erkenntnisse

## KI-Modelle

### Modell-Performance-Erkenntnisse
- **Erkenntnis:** llama3.1:8b ist überraschend gut für strukturierte Extraktion
- **Kontext:** Hermes-Extractor Tests
- **Datum:** 2024

### Embedding-Erkenntnisse
- **Erkenntnis:** nomic-embed-text ist für deutsche Texte ausreichend gut
- **Kontext:** Deutsche Dokument-Suche
- **Empfehlung:** Für hochwertige DE-Suche: bge-m3 nutzen

## Docker und Infrastruktur

### Container-Management
- **Erkenntnis:** NVIDIA Container Toolkit muss vor dem Docker-Start installiert sein
- **Erkenntnis:** `unless-stopped` ist sicherer als `always` für Entwicklung

## Qdrant

### Collection-Optimierung
- **Erkenntnis:** Separate Collections pro Zone verbessern Sicherheit und Performance
- **Erkenntnis:** Score-Threshold 0.7 ist ein guter Ausgangswert
