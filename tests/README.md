# tests – Test-Suite

**Zone:** WORKSPACE | **Verantwortlich:** kirobi-coder

## Zweck
Zentrale Test-Suite für Repo-, Service- und Sicherheitschecks.

## Test-Kategorien

| Verzeichnis | Test-Typ |
|-------------|---------|
| `unit/` | Fresh-clone-Baseline: offline laufende `pytest`-Suite inkl. `kirobi_core`, KIDI und Agent-Smoke-Tests |
| `integration/` | Live-Service-Tests mit laufendem Stack |
| `security/` | Zonen-, Policy- und Guardrail-spezifische Checks |
| `smoke/` | leichte End-to-End-/Erreichbarkeitsprüfungen |
| `retrieval/` | retrieval-spezifische Test-/Dokuhilfen |
| `conftest.py` | Fresh-clone-Bootstrap, optionales Ignorieren von Service-Contract-Tests, Registrierung von Services mit Bindestrich |

## Ausführen

```bash
# Fresh-clone-Baseline
python3 -m pytest tests/unit -q

# CI-äquivalenter Repo-Gate
make integration-test

# Live-Service-Integrationstests
python3 -m pytest tests/integration -v
```

## Aktuelle Baseline

- `python3 -m pytest tests/unit -q` läuft auf einem frischen Clone mit nur `pytest`
- in diesem Repo-Stand: **369 Tests grün**
- optionale Service-Contract-Tests werden ohne FastAPI-/Service-Dependencies nicht gesammelt
- `make integration-test` ist der statische Repo-Gate und führt **nicht** automatisch `tests/integration/` aus
