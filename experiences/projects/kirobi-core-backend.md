---
project_id: KIROBI-CORE-BACKEND
zone: WORKSPACE
status: aktiv
priority: hoch
started: 2024-01-01
agent: kirobi-coder
tags: [backend, api, python]
---

# Projekt: Kirobi Core Backend

## Ziel
Python-basiertes Backend-Service das die Kirobi-Logik implementiert: Routing, Kontext-Management, Event-Logging, Qdrant-Integration.

## Technologie-Stack
- Python 3.11+
- FastAPI
- SQLAlchemy (PostgreSQL)
- Qdrant-Client
- Langchain / LlamaIndex

## Milestones

- [ ] Projekt-Setup und Grundstruktur
- [ ] Qdrant-Client-Integration
- [ ] Routing-Engine
- [ ] Event-Logger
- [ ] Kontext-Manager
- [ ] REST-API-Endpoints
- [ ] Tests (>80% Coverage)

## Architektur-Entscheidungen

### ADR-001: FastAPI statt Flask
**Entscheidung:** FastAPI  
**Grund:** Native async-Support, automatische OpenAPI-Docs, bessere Performance

### ADR-002: SQLAlchemy für PostgreSQL
**Entscheidung:** SQLAlchemy 2.0  
**Grund:** Type-sichere Queries, gute Async-Unterstützung

## Nächste Schritte
1. Repository und Setup erstellen
2. Qdrant-Integration testen
3. Einfache Routing-Engine implementieren
