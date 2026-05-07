---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/security – Sicherheitstests

Sicherheitstests für das Kirobi-Ökosystem. Sie prüfen Zonen-Enforcement, Zugriffskontrolle, Prompt-Injection-Abwehr und die korrekte Behandlung sensibler Daten.

## Zweck

Sicherheitstests stellen sicher, dass das Fünf-Zonen-Modell technisch durchgesetzt wird und keine `FAMILY_PRIVATE`- oder `SACRED`-Daten unbeabsichtigt an externe Dienste gelangen oder in Logs erscheinen.

## Testbereiche

| Bereich | Was wird geprüft |
|---------|-----------------|
| Zonen-Enforcement | `can_write()`, `classify()` blockieren verbotene Zugriffe |
| Prompt Injection | Eingaben aus `sources/inbox/` werden nicht als Befehle ausgeführt |
| API-Datenleck | Keine FAMILY_PRIVATE/SACRED-Daten in externen API-Calls |
| Credential-Schutz | `.env`-Werte erscheinen nicht in Logs oder Responses |
| Auth-Grenzen | Unautorisierte Requests werden korrekt abgewiesen |

## Ausführen

```bash
# Alle Security-Tests
python -m pytest tests/security/ -v

# Nur Zonen-Tests (schnell, offline)
python -m pytest tests/unit/test_zones.py -v

# CI-Äquivalent
make integration-test
```

## Konventionen

- Tests dürfen **keine echten Secrets** enthalten – nur Dummy-Werte
- Jeder Test dokumentiert im Docstring, welches Sicherheitsprinzip er prüft
- Fehlschlagende Security-Tests blockieren den CI-Build

## Verwandte Tests

- `tests/unit/test_zones.py` – Zonen-Klassifizierung und Schreibrechte
- `tests/unit/test_audit.py` – Audit-Log-Integrität
- `tests/unit/test_auth_service.py` – Authentifizierungs-Service
