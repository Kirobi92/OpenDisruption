---
canon_id: ARCHITECTURE-MASTER
version: 1.0.0
zone: WORKSPACE
status: authoritative
---

# System-Architektur – Kirobi Canon Master

## Executive Summary
Kirobi / Disruptive OS ist eine lokale, Docker-basierte KI-Plattform mit 5-schichtigem Wissensmanagement, Multi-Agent-Orchestrierung und zonenbasierter Sicherheit.

## Architektur-Schichten

### Schicht 1: Infrastruktur
- Docker Compose für Service-Orchestrierung
- Ollama für LLM-Hosting
- Qdrant für Vektorsuche
- PostgreSQL für relationale Daten

### Schicht 2: Wissen
- 5-Ebenen-Modell: sources → extracts → clusters → canon → experiences
- Zonensystem: PUBLIC → WORKSPACE → FAMILY_PRIVATE → QUARANTINE → SACRED

### Schicht 3: Agenten
- 14 spezialisierte Agenten via Flowise
- kirobi-core als Supervisor
- Event-getriebene Kommunikation

### Schicht 4: Interfaces
- Open WebUI (Haupt-Interface)
- Voice (Whisper + TTS)
- API (geplant)
- Mobile (geplant)

## Technologie-Stack

| Kategorie | Technologie |
|-----------|------------|
| LLM-Hosting | Ollama |
| Vektordatenbank | Qdrant |
| Relationale DB | PostgreSQL 16 |
| Workflow | Flowise |
| Chat-UI | Open WebUI |
| Container | Docker Compose |
| Embedding | nomic-embed-text / bge-m3 |
