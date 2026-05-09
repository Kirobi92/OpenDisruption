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

## Abgedeckte Bereiche

- `kirobi_core`: CLI, Doctor, Scanner, Backlog, Zonen, Audit, Autonomie
- Agenten: Smoke-/Zone-Checks unter `tests/unit/agents/`
- KIDI: ContextDB- und Serve-Tests unter `tests/unit/kidi/`
- optionale Service-Contract-Tests für `auth`, `api`, `retrieval`, `embeddings`, `ingest`, `model-routing`, Media-Services, Telegram
- PWA-/Manifest- und Compose-adjacent Repo-Checks

## Ausführen

```bash
python3 -m pytest tests/unit -q

# fokussiert
python3 -m pytest tests/unit/test_zones.py -q

# nach Muster
python3 -m pytest tests/unit -k "zones or routing" -q
```

## Konventionen

- Jeder Test ist **offline** ausführbar – keine echten HTTP-Calls, keine laufenden Services
- Externe Abhängigkeiten werden mit `unittest.mock` gemockt
- Test-Dateien folgen dem Schema `test_[modul].py`
- `tests/conftest.py` hält die Fresh-Clone-Baseline stabil: optionale Service-Tests werden ohne FastAPI/httpx/asyncpg nicht gesammelt, und Bindestrich-Services werden für Imports registriert

## Aktuelle Baseline

`python3 -m pytest tests/unit -q` ist in diesem Repo-Stand grün mit **369** Tests.
