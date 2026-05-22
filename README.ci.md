# CI-Referenz: Kirobi APK GitHub Actions

> **Maintenance-Dokument** — Stand: 2026-05-22 | OPE-249

---

## Workflow-Übersicht (7 Workflows)

| # | Datei | Name | Trigger | Ø Laufzeit | Letzter Status |
|---|---|---|---|---|---|
| 1 | `ci.yml` | CI | push→main, pull_request | ~3 min | ✅ grün |
| 2 | `install-test.yml` | Installer | push/PR auf install.sh, infra/scripts/**, config/templates/** | ~2 min | ✅ grün |
| 3 | `lint-workflows.yml` | Lint GitHub Actions Workflows | push/PR auf .github/workflows/**, workflow_dispatch | ~2 min | ✅ grün |
| 4 | `nightly-audit.yml` | nightly-audit | schedule 03:00 UTC täglich, workflow_dispatch | ~5 min | ✅ grün |
| 5 | `story-nav-e2e.yml` | Story Navigation E2E (Playwright) | push/PR auf frontend/src/stories/**, tests/e2e/**, workflow_dispatch | ~4 min | ✅ grün |
| 6 | `unit-tests.yml` | Frontend Unit Tests (Vitest) | push/PR auf frontend/src/**, frontend/package.json, frontend/vite.config.ts, workflow_dispatch | ~2 min | ✅ grün |
| 7 | `weekly-download-report.yml` | Weekly APK Download Report | schedule Mo 09:00 UTC, workflow_dispatch (dry_run Option) | ~1 min | ✅ grün |

---

## Detailbeschreibungen

### 1. `ci.yml` — Haupt-CI

**Trigger:**
- `push` auf `main`
- `pull_request` (alle Branches)

**Jobs:**
- **unit-tests** (Python 3.12): Installiert Kern-Abhängigkeiten (`pytest`, `fastapi`, `httpx`, etc.) → `python -m pytest tests/unit -q` → Job-Summary mit PASS/FAIL-Badge + Test-Datei-Liste
- **smoke-tests** (optional): Schneller Smoke-Durchlauf für kritische Endpunkte

**Besonderheiten:**
- Notification via Telegram wenn `KIROBI_UNIT_NOTIFY_SUCCESS=true` (GitHub Variable)
- Job-Summary enthält Badge-Link + Test-File-Liste für schnelle Orientierung
- Permissions: `contents: read`

**Typische Laufzeit:** ~3 Minuten

---

### 2. `install-test.yml` — Installer-Validierung

**Trigger:**
- `push`/`pull_request` auf `main` — nur bei Änderungen an:
  - `install.sh`
  - `infra/scripts/**`
  - `config/templates/**`
  - `.github/workflows/install-test.yml`

**Jobs:**
- **shellcheck**: `shellcheck -S warning install.sh infra/scripts/*.sh`
- **installer-help**: `bash install.sh --version` + `bash install.sh --help` (Dry-Run-Verifikation)
- **dry-run** (optional): `bash install.sh --dry-run --no-clone --auto --skip-checks --no-pull --no-models --no-start --profile=cpu`

**Besonderheiten:**
- Läuft NUR wenn relevante Dateien geändert wurden (path-Filter) → spart CI-Minuten
- shellcheck mit `-S warning` filtert nur Warning+ (kein style-Rauschen)
- Permissions: `contents: read`

**Typische Laufzeit:** ~2 Minuten

---

### 3. `lint-workflows.yml` — Workflow-Lint

**Trigger:**
- `push`/`pull_request` auf `main` — nur bei `.github/workflows/**`
- `workflow_dispatch` (manuell)

**Jobs:**
- **actionlint** (actionlint 1.7.12 + shellcheck):
  1. shellcheck installieren
  2. actionlint installieren (via GitHub Releases, fester Tag)
  3. shellcheck-Scan aller Shell-Skripte (SC2102/SC2001/SC2086 Severity-Filter)
  4. actionlint auf alle `.github/workflows/*.yml`
  5. WORKFLOW_COUNT via Bash-Array-Glob berechnen: `WORKFLOW_FILES=(.github/workflows/*.yml)` → `WORKFLOW_COUNT=${#WORKFLOW_FILES[@]}`
  6. SC_ISSUE_COUNT als Step-Output exportieren
  7. Job-Summary mit Badges, Zählern und Link zu README.ci.md

**WORKFLOW_COUNT Mechanismus:**
```bash
WORKFLOW_FILES=(.github/workflows/*.yml)
WORKFLOW_COUNT=${#WORKFLOW_FILES[@]}
```
→ Automatisch skalierend — kein Hardcode, kein manuelles Tracking.

**SC_ISSUE_COUNT:**
```yaml
echo "sc_issue_count=$SC_ISSUE_COUNT" >> "$GITHUB_OUTPUT"
```
- `SC_ISSUE_COUNT=0` → sauber ✅
- `SC_ISSUE_COUNT>0` → Findings in Step-Logs prüfen
- Telegram-Alert-Schwelle: `KIROBI_SC_ALERT_THRESHOLD` in `.env` (Standard: 0)

**Typische Laufzeit:** ~2 Minuten

---

### 4. `nightly-audit.yml` — Nacht-Audit

**Trigger:**
- `schedule: cron: "0 3 * * *"` (03:00 UTC, täglich)
- `workflow_dispatch` (manuell auslösbar)

**Jobs:**
- **python-tests** (Python 3.11):
  - `python -m pytest tests/unit -q`
  - `make integration-test` (continue-on-error)
  - `pip-audit --strict || true` (Dependency-Security-Advisory)
- **shell-lint**: shellcheck auf `install.sh` + `infra/scripts/*.sh`

**Besonderheiten:**
- `permissions: issues: write` — kann GitHub Issues anlegen bei kritischen Findings
- `pip-audit` läuft advisory-only (`|| true`) — blockiert nicht, aber loggt CVEs
- `make integration-test` deckt: Unit-Tests, offline doctor, Compose-Validierung, Script-Syntax, FastAPI py_compile, PWA-Manifest-Checks

**Typische Laufzeit:** ~5 Minuten

---

### 5. `story-nav-e2e.yml` — Playwright E2E

**Trigger:**
- `push`/`pull_request` auf `main` — bei Änderungen an:
  - `tests/e2e/test_story_nav_e2e.py`
  - `tests/e2e/conftest.py`
  - `frontend/src/stories/**`
  - `frontend/src/StoryIndex.tsx`
  - `frontend/src/App.tsx`
  - `.github/workflows/story-nav-e2e.yml`
- `workflow_dispatch` (manuell)

**Jobs:**
- **check-labels**: Bei `pull_request` nur ausführen wenn Label `e2e` oder `frontend` gesetzt → verhindert unnötige E2E-Runs auf trivialen PRs
- **playwright-e2e**: Installiert Node.js 22, Playwright-Browser, startet Frontend Dev-Server, führt `pytest tests/e2e/` aus

**Besonderheiten:**
- `concurrency: group: story-nav-e2e-${{ github.ref }}`, `cancel-in-progress: true` → kein Queue-Stau
- Tests prüfen alle `STORY_ROUTES_META`-Einträge auf Deep-Link-Navigierbarkeit
- Artifact-Upload für Playwright-Traces bei Fehler (Git-Exit-Code-128-Warnung bekannt, harmlos)
- Permissions: `contents: read`

**Typische Laufzeit:** ~4 Minuten

---

### 6. `unit-tests.yml` — Frontend Vitest

**Trigger:**
- `push`/`pull_request` auf `main` — bei Änderungen an:
  - `frontend/src/**`
  - `frontend/package.json`
  - `frontend/vite.config.ts`
  - `frontend/tsconfig*.json`
  - `.github/workflows/unit-tests.yml`
- `workflow_dispatch` (manuell)

**Jobs:**
- **vitest** (Node.js 22, working-directory: frontend, timeout: 10 min):
  - `npm ci`
  - `npx vitest run --reporter=verbose`
  - Job-Summary mit Test-Ergebnissen + Badge
  - Optionale Telegram-Notification wenn `KIROBI_UNIT_NOTIFY_SUCCESS=true`

**Besonderheiten:**
- `concurrency: group: unit-tests-${{ github.ref }}`, `cancel-in-progress: true`
- Tested: `SystemModule`, `ScAlertsPanel`, `StoryMusicHealthConfig`, alle Story-Snapshots
- Node.js `>=22` Requirement in `vite.config.ts` `engines` — verhindert Node 20-Deprecation-Warnings
- Permissions: `contents: read`

**Typische Laufzeit:** ~2 Minuten

---

### 7. `weekly-download-report.yml` — APK Download-Report

**Trigger:**
- `schedule: cron: '0 9 * * 1'` (jeden Montag 09:00 UTC)
- `workflow_dispatch` mit optionalem `dry_run: boolean` Input

**Jobs:**
- **download-report** (Python 3.11, timeout: 10 min):
  1. GitHub Releases API: aktuelle Download-Zahlen aller APK-Assets abrufen
  2. History-JSON (`apk-download-history.json`) aktualisieren + committen
  3. Vergleichs-Report (Woche-zu-Woche Delta) als Markdown formatieren
  4. Telegram-Nachricht an Sven (Chat-ID: `1066082496`) mit Report-Summary

**Besonderheiten:**
- `permissions: contents: write` — für History-JSON Commit direkt auf `main`
- `dry_run=true` → Report wird generiert aber NICHT via Telegram gesendet
- `concurrency: cancel-in-progress: false` → alte Runs nicht abbrechen (History-Commits!)
- Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (Fallback: `1066082496`)

**Typische Laufzeit:** ~1 Minute

---

## WORKFLOW_COUNT Tracking

### Dry-Run Protokoll: 6→7 (Run 141, 2026-05-21)

| Zustand | Glob-Ergebnis | WORKFLOW_COUNT |
|---|---|---|
| **Vorher** (6 Workflows) | `ci.yml`, `install-test.yml`, `lint-workflows.yml`, `nightly-audit.yml`, `story-nav-e2e.yml`, `weekly-download-report.yml` | **6** ✅ |
| **Mock hinzugefügt** (`_mock-test.yml`) | + 1 Datei | **7** ✅ |
| **Mock entfernt** | zurück auf 6 Dateien | **6** ✅ |

### Produktiv-Update: 6→7 via unit-tests.yml (Stand: 2026-05-22)

| Event | WORKFLOW_COUNT | Trigger |
|---|---|---|
| Vor unit-tests.yml | 6 | — |
| Nach unit-tests.yml Commit | **7** | Automatisch via Glob-Array ✅ |

**Bestätigt:** `WORKFLOW_COUNT=${#WORKFLOW_FILES[@]}` zählt live — keine manuelle Pflege erforderlich.

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

## Quick-Reference: Lokale Debugging-Befehle

```bash
# Workflow lokal linten
actionlint .github/workflows/DATEI.yml

# shellcheck lokal (gleiche Einstellungen wie CI)
shellcheck -S warning install.sh infra/scripts/*.sh

# Unit-Tests lokal (Python)
python -m pytest tests/unit -q

# Frontend Unit-Tests lokal (Vitest)
cd frontend && npx vitest run

# E2E lokal
cd tests/e2e && pytest test_story_nav_e2e.py -v
```

## Nächste Schritte

- Bei neuen Workflows: Datei in `.github/workflows/` ablegen → `WORKFLOW_COUNT` passt sich automatisch an
- Bei shellcheck-Findings: `actionlint .github/workflows/DATEI.yml` lokal ausführen
- SC_ISSUE_COUNT Dashboard-Integration: `KIROBI_SC_ALERT_THRESHOLD` in `.env` konfigurieren
- Bei Dependabot-Alerts: Workflow `ci.yml` + `nightly-audit.yml` pip-audit-Output prüfen
