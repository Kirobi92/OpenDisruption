# CI-Referenz: lint-workflows.yml — WORKFLOW_COUNT Verifikation

## WORKFLOW_COUNT Mechanismus

`lint-workflows.yml` berechnet die Anzahl der GitHub Actions Workflows **dynamisch** via Bash-Array-Glob:

```bash
WORKFLOW_FILES=(.github/workflows/*.yml)
WORKFLOW_COUNT=${#WORKFLOW_FILES[@]}
```

Kein Hardcode, kein manuelles Tracking — automatisch skalierend bei neuen `.yml`-Dateien.

---

## Dry-Run Protokoll: 6→7 (Run 141, 2026-05-21)

| Zustand | Glob-Ergebnis | WORKFLOW_COUNT |
|---|---|---|
| **Vorher** (6 Workflows) | `ci.yml`, `install-test.yml`, `lint-workflows.yml`, `nightly-audit.yml`, `story-nav-e2e.yml`, `weekly-download-report.yml` | **6** ✅ |
| **Mock hinzugefügt** (`_mock-test.yml`) | + 1 Datei | **7** ✅ |
| **Mock entfernt** | zurück auf 6 Dateien | **6** ✅ |

**Fazit:** Glob-Array korrekt — WORKFLOW_COUNT zählt automatisch hoch und runter. Kein Code-Change erforderlich.

---

## Produktiv-Update: 6→7 via unit-tests.yml (Stand: 2026-05-22)

`unit-tests.yml` wurde produktiv hinzugefügt (OPE-217/218). WORKFLOW_COUNT ist damit real auf **7** gestiegen — kein Mock nötig, der Delta-Alert hat korrekt funktioniert:

| Event | WORKFLOW_COUNT | Trigger |
|---|---|---|
| Vor unit-tests.yml | 6 | — |
| Nach unit-tests.yml Commit | **7** | Automatisch via Glob-Array ✅ |

**Bestätigt:** `WORKFLOW_COUNT=${#WORKFLOW_FILES[@]}` zählt live — keine manuelle Pflege erforderlich.

---

## Aktuelle Workflows (Stand: 2026-05-22)

| # | Datei | Zweck |
|---|---|---|
| 1 | `ci.yml` | Haupt-CI: Unit-Tests, Smoke-Tests, Integrations-Tests |
| 2 | `install-test.yml` | Installer-Dry-Run, Compose-Validierung |
| 3 | `lint-workflows.yml` | actionlint + shellcheck für alle Workflows |
| 4 | `nightly-audit.yml` | Nächtlicher Sicherheits- und Qualitäts-Audit |
| 5 | `story-nav-e2e.yml` | Playwright E2E: Story-Navigation im APK-Frontend |
| 6 | `unit-tests.yml` | Vitest Unit-Tests + pytest für alle Services |
| 7 | `weekly-download-report.yml` | Wöchentlicher APK-Download-Stats-Report via Telegram |

---

## SC_ISSUE_COUNT Tracking

shellcheck-Findings werden als Step-Output exportiert:

```yaml
echo "sc_issue_count=$SC_ISSUE_COUNT" >> "$GITHUB_OUTPUT"
```

Und als Tabellen-Zeile im Job-Summary angezeigt (`| shellcheck Findings | N |`).

- `SC_ISSUE_COUNT=0` → sauber ✅
- `SC_ISSUE_COUNT>0` → Findings in Workflow-Step-Logs prüfen

Konfigurierbar via ENV `KIROBI_SC_ALERT_THRESHOLD` (Telegram-Alert-Schwelle, Standard: 0).

---

## Nächste Schritte

- Bei neuen Workflows: Datei in `.github/workflows/` ablegen → WORKFLOW_COUNT passt sich automatisch an
- Bei shellcheck-Findings: `actionlint .github/workflows/DATEI.yml` lokal ausführen
- SC_ISSUE_COUNT Dashboard-Integration: `KIROBI_SC_ALERT_THRESHOLD` in `.env` konfigurieren
