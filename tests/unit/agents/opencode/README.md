---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Unit-Tests: opencode-Agent

Pytest-Tests für den `opencode`-Agenten — prüfen Smoke-Verhalten und
Zonen-Sicherheitsregeln (Zone-Refusal-Policy).

## Tests ausführen

```bash
python -m pytest tests/unit/agents/opencode -q
```

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `test_handle_smoke.py` | Basis-Smoke-Test: Agent startet und antwortet |
| `test_zone_refusal.py` | Sicherheitstest: SACRED/FAMILY_PRIVATE-Anfragen werden abgelehnt |
| `__init__.py` | Package-Marker |

## Hinweis

`test_zone_refusal.py` ist sicherheitskritisch — Fehlschläge hier bedeuten
potenzielle Zonen-Policy-Verletzungen und müssen sofort untersucht werden.
