---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/unit – Unit-Tests

Schnelle, isolierte Tests für einzelne Funktionen und Module des Kirobi-Systems. Laufen vollständig offline ohne laufende Services oder Netzwerkzugriff – alle externen Abhängigkeiten werden gemockt.

## Zweck

Unit-Tests sind die erste Verteidigungslinie. Sie prüfen einzelne Funktionen in Isolation und geben innerhalb von Sekunden Feedback. Sie sind die Grundlage des CI-Checks (`make integration-test`).

## Enthaltene Test-Dateien

| Datei | Was wird getestet |
|-------|------------------|
| `test_zones.py` | Zonen-Klassifizierung, `can_write()`, `classify()` |
| `test_audit.py` | Audit-Log-Integrität, Append-Only-Verhalten |
| `test_auth_service.py` | Authentifizierungs-Service, JWT-Validierung |
| `test_api_service.py` | FastAPI-Endpunkte, Request/Response-Schemas |
| `test_autonomous.py` | Autonomer Supervisor, Task-Ausführung |
| `test_backlog.py` | Backlog-Verwaltung, Task-Priorisierung |
| `test_bridge.py` | Interne Service-Bridge-Kommunikation |
| `test_cli.py` | `kirobi_core`-CLI-Befehle |
| `test_doctor.py` | System-Health-Check (`kirobi_core doctor`) |
| `test_embeddings_service.py` | Embedding-Generierung (gemockt) |
| `test_ingest_service.py` | Ingestion-Pipeline, Dokument-Verarbeitung |
| `test_interview.py` | Family-Interviewer-Logik |
| `test_keycodi.py` | KeyCodi-Orchestrator-Funktionen |
| `test_model_routing_service.py` | Modell-Routing, Fallback-Logik |
| `test_notify.py` | Benachrichtigungs-Service |
| `test_orchestrator.py` | Agent-Orchestrierung |
| `test_pwa.py` | PWA-Manifest und Icon-Validierung |
| `test_registry.py` | Agent-Registry |
| `test_retrieval_service.py` | Retrieval-Service (Qdrant gemockt) |
| `test_scanner.py` | Datei-Scanner, Zonen-Erkennung |
| `test_services.py` | Service-Grundfunktionen |
| `test_telegram_service.py` | Telegram-Bot-Integration |

## Ausführen

```bash
# Alle Unit-Tests
python -m pytest tests/unit/ -q

# Einzelne Datei
python -m pytest tests/unit/test_zones.py -v

# Nach Stichwort filtern
python -m pytest tests/unit/ -k "zones or routing" -v

# Mit Coverage
python -m pytest tests/unit/ --cov=kirobi_core --cov-report=term-missing
```

## Konventionen

- Jeder Test ist **offline** ausführbar – keine echten HTTP-Calls, keine laufenden Services
- Externe Abhängigkeiten werden mit `unittest.mock` oder `pytest-mock` gemockt
- Test-Dateien folgen dem Schema `test_[modul].py`
- Docstrings erklären **warum** ein Verhalten getestet wird, nicht nur was

## Verwandte Verzeichnisse

- `tests/integration/` – Tests mit laufenden Services
- `tests/security/` – Sicherheits- und Zonen-Tests
- `kirobi_core/` – Getestete Python-Bibliothek
