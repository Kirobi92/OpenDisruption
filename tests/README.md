# tests – Test-Suite

**Zone:** WORKSPACE | **Verantwortlich:** kirobi-coder

## Zweck
Zentrale Test-Suite für das gesamte Kirobi-System.

## Test-Kategorien

| Verzeichnis | Test-Typ |
|-------------|---------|
| `unit/` | Unit-Tests für einzelne Funktionen |
| `integration/` | Integrations-Tests zwischen Komponenten |
| `e2e/` | End-to-End Tests |
| `agents/` | Agent-Behavior-Tests |
| `performance/` | Performance- und Last-Tests |

## Ausführen

```bash
# Alle Tests
pytest tests/

# Nur Unit-Tests
pytest tests/unit/

# Mit Coverage
pytest --cov=. tests/
```
