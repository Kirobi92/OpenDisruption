---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# tests/smoke

Smoke-Tests: schnelle Grundprüfungen, ob das System nach einem Deploy noch grundlegend funktioniert.

## Zweck

Smoke-Tests prüfen nicht die Korrektheit von Business-Logik — sie prüfen, ob die wichtigsten Endpunkte erreichbar sind und keine offensichtlichen Fehler vorliegen. Sie laufen nach jedem Deploy als erster Indikator.

## Abgrenzung

| Test-Typ | Prüft | Geschwindigkeit |
|----------|-------|-----------------|
| **Smoke** | Erreichbarkeit, HTTP 200, kein Crash | Sekunden |
| **Integration** | Zusammenspiel mehrerer Services | Minuten |
| **Unit** | Einzelne Funktionen isoliert | Millisekunden |

## Ausführen

```bash
# Alle Smoke-Tests
python -m pytest tests/smoke/ -v

# Nur Health-Checks
python -m pytest tests/smoke/ -k health -q
```

## Voraussetzungen

Smoke-Tests setzen laufende Services voraus. Vor dem Ausführen:

```bash
docker compose ps   # Services prüfen
bash infra/scripts/healthcheck.sh  # Infrastruktur-Check
```

## Bekannte Einschränkungen

Smoke-Tests schlagen fehl, wenn Services nicht gestartet sind — das ist beabsichtigt. Sie sind kein Ersatz für Unit-Tests.
