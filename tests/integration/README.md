---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/integration

Integrationstests: prüfen das Zusammenspiel mehrerer Services und Komponenten.

## Zweck

Integrationstests stellen sicher, dass Services korrekt miteinander kommunizieren — z. B. dass der API-Service Daten korrekt in PostgreSQL schreibt, der Retrieval-Service Qdrant korrekt abfragt oder der Auth-Service JWT-Tokens ausstellt, die andere Services akzeptieren.

## Abgrenzung

| Test-Typ | Prüft | Voraussetzung |
|----------|-------|---------------|
| **Unit** | Einzelne Funktionen isoliert | Keine Services nötig |
| **Smoke** | Erreichbarkeit / kein Crash | Laufende Services |
| **Integration** | Service-übergreifende Abläufe | Laufende Services + Datenbank |

## Ausführen

```bash
# Alle Integrationstests
python -m pytest tests/integration/ -v

# CI-äquivalenter Check (inkl. Unit-Tests)
make integration-test
```

## Voraussetzungen

```bash
# Services starten (mindestens: api, auth, postgres, qdrant)
docker compose up -d api auth postgres qdrant

# Env-Variablen prüfen
bash infra/scripts/validate-env.sh
```

## Konventionen

- Test-Dateien: `test_{service}_{szenario}.py`
- Keine echten FAMILY_PRIVATE- oder SACRED-Daten in Tests
- Fixtures für Testdaten in `conftest.py` ablegen
- Tests müssen nach sich selbst aufräumen (Datenbank-Rollback oder Teardown)
