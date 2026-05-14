---
zone: WORKSPACE
created: 2026-05-14
version: 1.0
status: ACTIVE
---

# TESTING_STRATEGY.md

## Status quo
- 52 Test-Dateien, alle in `tests/unit/`
- 574 Tests grün (Stand 2026-05-14, `python -m pytest tests/unit -q`)
- Test-Subjekt zu ~95 % `kirobi_core/` (Python-CLI/Lib)
- **14/16 Backend-Services ohne dedizierte Unit-Tests**
- Ausnahmen: `analytics-service` (10), `orchestrator` (3)
- Kein Coverage-Report
- Keine Integration-Tests gegen laufende Container
- Keine E2E-Browser-Tests
- Keine Contract-Tests zwischen Services

## Ziel-Pyramide

```
         ┌─────────────┐
         │     E2E     │  10 Tests (Playwright, monatl. CI-Job)
         ├─────────────┤
         │ Integration │  ~50 Tests (HTTP gegen `docker compose up`)
         ├─────────────┤
         │  Contract   │  ~30 Tests (Service-↔-Service-Schemas)
         ├─────────────┤
         │    Unit     │  600 → 1 200 Tests (kirobi_core + jeder Service)
         └─────────────┘
```

## Phase 1: Coverage-Sichtbarkeit (Sprint 1)

### Tooling
```bash
pip install pytest-cov coverage[toml]
```

### `pyproject.toml`
```toml
[tool.coverage.run]
source = ["kirobi_core", "services"]
omit = [
  "*/tests/*",
  "*/__pycache__/*",
  "services/*/Dockerfile",
]

[tool.coverage.report]
exclude_lines = [
  "pragma: no cover",
  "if __name__ == .__main__.:",
  "raise NotImplementedError",
]
fail_under = 30   # Sprint 1: 30 %, Sprint 2: 50 %, Sprint 3: 70 %
```

### Makefile
```makefile
test-coverage:
	python -m pytest tests/ --cov --cov-report=term --cov-report=html

ci-coverage:
	python -m pytest tests/ --cov --cov-report=xml --cov-fail-under=30
```

### CI-Workflow (`.github/workflows/test.yml`)
```yaml
- name: Tests + Coverage
  run: make ci-coverage
- uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
```

## Phase 2: Service-Unit-Tests (Sprint 2)

Pro Service mindestens:
- Health-Endpoint
- Happy-Path für jede Hauptroute
- Eine Edge-Case (404, 422, 500)
- Eine Auth-Test (wenn Auth implementiert)

### Priorisierung
| Service | LOC | Risiko ohne Tests | Priorität |
|---|---|---|---|
| api | 2 262 | sehr hoch | **P0** |
| auth | 790 | sehr hoch | **P0** |
| ingest | 678 | hoch | **P0** |
| retrieval | 362 | hoch | **P0** |
| personal-agents | 563 | hoch | **P1** |
| voice-processing | 1 880 | mittel | **P1** |
| telegram | 4 761 | mittel | **P1** |
| model-routing | 185 | mittel | **P1** |
| embeddings | 466 | mittel | **P2** |
| image/music/video-generation | 1 917 | niedrig | **P2** |
| media-processing | 313 | niedrig | **P2** |
| nutzi | 1 001 | mittel | **P2** |
| hermes-runtime | 316 | niedrig | **P2** |

### Test-Vorlage (`tests/services/test_api_health.py`)
```python
import pytest
from fastapi.testclient import TestClient
from services.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
```

## Phase 3: Integration-Tests (Sprint 3)

### Setup
- `tests/integration/conftest.py` startet `docker compose up -d` bei `pytest`-Beginn
- Tests sprechen gegen `127.0.0.1:<port>` direkt
- Cleanup: `docker compose down -v` nur bei Bedarf

### Smoke-Suite
```python
# tests/integration/test_smoke.py
SERVICES = [
  ("auth", 8002), ("api", 8003), ("embeddings", 8004),
  ("retrieval", 8006), ("ingest", 8007), ("model-routing", 8009),
  ("analytics", 8010), ("image-generation", 8011),
  ("media-processing", 8012), ("music-generation", 8013),
  ("video-generation", 8014), ("personal-agents", 8017),
]

@pytest.mark.parametrize("name,port", SERVICES)
def test_health(name, port):
    r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=5)
    assert r.status_code == 200, f"{name} unhealthy"
```

### Zone-Test
```python
def test_sacred_returns_403():
    r = httpx.get("http://127.0.0.1:8006/search?zone=SACRED&q=any")
    assert r.status_code == 403
```

## Phase 4: Contract-Tests

Pydantic-Modelle aus jedem Service als JSON-Schema exportieren, gegen
Konsumenten validieren (z.B. `api → personal-agents`).

Vorschlag: **Schemathesis** für OpenAPI-basiertes Property-Testing.

## Phase 5: E2E (optional)

- Playwright gegen `apps/web`
- Login mit `samira` → Chat → Antwort enthält keine erfundenen Geburtstags-Fakten
- Dauer pro Lauf: < 5 min

## Test-Daten / Fixtures

- `tests/fixtures/` für Beispiel-Markdown, JSON, Audio
- Kein Echtdaten von `experiences/family/` oder `sacred/` in Tests
- Postgres-Test-Container mit eigenen Schema-Dumps

## Coverage-Ziele pro Quartal

| Quartal | Coverage-Ziel | Maßnahme |
|---|---|---|
| Q1 | 30 % | API + Auth + Ingest + Retrieval Tests |
| Q2 | 50 % | + voice-processing, telegram, generation-services |
| Q3 | 70 % | + Integration-Suite, Contract-Tests |
| Q4 | 80 % | E2E-Suite, Property-Tests |

## CI-Erweiterungen

1. `pytest --cov --cov-fail-under=30` als Pflicht-Check
2. `pip-audit` in CI
3. `npm audit --audit-level=high` in `apps/`-Workflows
4. Container-Image-Build pro Service in CI (jetzt nicht vorhanden)
5. Cosign-Signing (langfristig)

## Anti-Patterns

- ❌ Tests die `time.sleep()` verwenden ohne Grund
- ❌ Tests die Echtdaten aus `experiences/family/` einlesen
- ❌ Tests die direkt gegen Production-Postgres laufen
- ❌ Tests ohne `assert` (Smoke ohne Validation)
- ❌ Über 1 000 LOC Test pro Datei (splitten)
