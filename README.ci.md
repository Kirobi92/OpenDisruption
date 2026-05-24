# CI-Referenz: Kirobi APK GitHub Actions

> **Maintenance-Dokument** — Stand: 2026-05-24 | OPE-301

---

## Workflow-Übersicht (9 Workflows)

| # | Datei | Name | Trigger | Ø Laufzeit | Letzter Status |
|---|---|---|---|---|---|
| 1 | `build-release-apk.yml` | Build Release APK | workflow_dispatch (manuell, version_suffix Input) | ~8 min | ✅ |
| 2 | `ci.yml` | Kirobi Backend CI | push→main, pull_request | ~3 min | ✅ |
| 3 | `e2e-keyboard-nav.yml` | E2E Keyboard & Swipe Navigation | push/PR auf tests/e2e/**, workflow_dispatch | ~4 min | ✅ |
| 4 | `integration-tests.yml` | kirobi-backend-integration-tests | push/PR auf backend/**, workflow_dispatch | ~3 min | ✅ |
| 5 | `lint-frontend.yml` | Frontend ESLint (oxc-Gate) | push/PR auf frontend/src/**, eslint.config.js, workflow_dispatch | ~1 min | ✅ |
| 6 | `lint-workflows.yml` | Lint & Count Workflows | push/PR auf .github/workflows/**, workflow_dispatch | ~2 min | ✅ |
| 7 | `story-nav-e2e.yml` | Story Navigation E2E (Playwright) | push/PR auf frontend/src/stories/**, tests/e2e/**, workflow_dispatch | ~4 min | ✅ |
| 8 | `unit-tests.yml` | Frontend Unit Tests (Vitest) | push/PR auf frontend/src/**, frontend/package.json, frontend/vite.config.ts, workflow_dispatch | ~2 min | ✅ |
| 9 | `weekly-download-report.yml` | Weekly APK Download Report | schedule Mo 09:00 UTC, workflow_dispatch (dry_run Option) | ~1 min | ✅ |

---

## Detailbeschreibungen

### 1. `build-release-apk.yml` — Release APK Build

**Trigger:**
- `workflow_dispatch` (manuell) mit optionalem `version_suffix`-Input

**Jobs:**
- **build**: Node.js + JDK Setup → `npm ci` → `npm run build` → Capacitor Sync → Android Release APK Build → APK signieren → GitHub Release erstellen + APK hochladen

**Besonderheiten:**
- Erfordert Secrets: `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`
- APK wird als GitHub Release Asset veröffentlicht
- Permissions: `contents: write` (für GitHub Release)

**Typische Laufzeit:** ~8 Minuten

---

### 2. `ci.yml` — Kirobi Backend CI

**Trigger:**
- `push` auf `main`
- `pull_request` (alle Branches)

**Jobs:**
- **test** (Python 3.11/3.12): `pip install -r requirements.txt` → `python -m pytest` → Job-Summary
- Optionale Telegram-Notification wenn `KIROBI_UNIT_CI_NOTIFY_SUCCESS=true`

**Besonderheiten:**
- Notification via `KIROBI_TELEGRAM_BOT_TOKEN` Secret + Chat-ID `1066082496`
- Dependabot-Vulnerabilities werden via `pip-audit` oder GitHub Security erfasst
- Permissions: `contents: read`

**Typische Laufzeit:** ~3 Minuten

---

### 3. `e2e-keyboard-nav.yml` — E2E Keyboard & Swipe Navigation

**Trigger:**
- `push`/`pull_request` auf `main` — bei Änderungen an:
  - `tests/e2e/**`
  - `frontend/src/**`
  - `.github/workflows/e2e-keyboard-nav.yml`
- `workflow_dispatch` (manuell)

**Jobs:**
- **playwright**: Node.js 22 + Playwright → Dev-Server starten → E2E Tests für Keyboard-Navigation und Swipe-Gesten

**Besonderheiten:**
- `concurrency: cancel-in-progress: true` → kein Queue-Stau
- Artifact-Upload für Playwright-Traces bei Fehler
- Permissions: `contents: read`

**Typische Laufzeit:** ~4 Minuten

---

### 4. `integration-tests.yml` — Backend Integration Tests

**Trigger:**
- `push`/`pull_request` auf `main` — bei Änderungen an:
  - `backend/**`
  - `tests/integration/**`
  - `.github/workflows/integration-tests.yml`
- `workflow_dispatch` (manuell)

**Jobs:**
- **integration**: Python 3.11 → Backend starten → Integration Tests gegen laufenden Server

**Besonderheiten:**
- Backend-Server wird als Subprocess innerhalb des CI-Jobs gestartet
- Health-Check vor Test-Ausführung
- Permissions: `contents: read`

**Typische Laufzeit:** ~3 Minuten

---

### 5. `lint-frontend.yml` — Frontend ESLint (oxc-Gate)

**Trigger:**
- `push`/`pull_request` auf `main`/`master` — bei Änderungen an:
  - `frontend/src/**`
  - `frontend/package.json`, `frontend/package-lock.json`
  - `frontend/eslint.config.js`
  - `frontend/tsconfig*.json`
  - `.github/workflows/lint-frontend.yml`
- `workflow_dispatch` (manuell)

**Jobs:**
- **eslint** (Node.js 22, working-directory: frontend, timeout: 5 min):
  - `npm ci`
  - `npm run lint` (ESLint mit `@typescript-eslint/consistent-type-imports` als Error-Level)
  - Job-Summary mit ESLint-Ergebnissen + oxc-Gate-Status
  - BLOCKIERT den PR wenn `import type { X }` Statements gefunden werden (oxc-Schutz-Gate)

**oxc-Gate Mechanismus:**
- ESLint-Regel `@typescript-eslint/consistent-type-imports: error` prüft auf `import type { X }`-Syntax
- Diese Syntax ist inkompatibel mit oxc/rolldown Parser, der in `@vitest/coverage-v8` verwendet wird
- Bei Fund → PR wird mit Exit 1 geblockt, Job-Summary zeigt betroffene Dateien + `npm run lint:fix` Hinweis
- Bei Clean → PR passiert das Gate ✅

**Besonderheiten:**
- Nur `consistent-type-imports`-Fehler blockieren den Build (oxc-Gate)
- Pre-existing Issues (no-empty, react-hooks/exhaustive-deps) werden in Summary gelistet, blockieren aber nicht
- `concurrency: group: lint-frontend-${{ github.ref }}`, `cancel-in-progress: true`
- Permissions: `contents: read`

**Typische Laufzeit:** ~1 Minute

---

### 6. `lint-workflows.yml` — Workflow-Lint & Count

**Trigger:**
- `push`/`pull_request` auf `main` — nur bei `.github/workflows/**`
- `workflow_dispatch` (manuell)

**Jobs:**
- **count-and-lint**:
  1. Aktuelle Workflow-Anzahl via `find .github/workflows -maxdepth 1 -name "*.yml"` ermitteln
  2. Delta-Check gegen `WORKFLOW_COUNT_REF` (aktuell: `8`) — Alert bei Delta ≥2
  3. yamllint auf alle Workflow-YAMLs
  4. actionlint 1.7.12 mit shellcheck-Integration (SC_ALERT non-blocking)
  5. README.ci.md in Job-Summary verlinken

**WORKFLOW_COUNT_REF:**
```
WORKFLOW_COUNT_REF: "8"
# Stand: 2026-05-22 (OPE-248)
# Workflows: ci, e2e-keyboard-nav, integration-tests, weekly-download-report,
#            build-release-apk, story-nav-e2e, unit-tests, lint-workflows
```

**SC_ALERT Mechanismus:**
- SC2086/info/style/warning Findings → SC_ALERT in Job-Summary (non-blocking)
- Nur echte shellcheck-Errors → LINT FAIL

**Telegram-Alert bei Delta ≥2:** sendet Warnung an Chat-ID `1066082496`

**Typische Laufzeit:** ~2 Minuten

---

### 7. `story-nav-e2e.yml` — Story Navigation E2E (Playwright)

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
- **check-labels**: Bei `pull_request` nur ausführen wenn Label `e2e` oder `frontend` gesetzt
- **playwright-e2e**: Node.js 22 + Playwright → Frontend Dev-Server → `pytest tests/e2e/`

**Besonderheiten:**
- `concurrency: group: story-nav-e2e-${{ github.ref }}`, `cancel-in-progress: true`
- Tests prüfen alle `STORY_ROUTES_META`-Einträge auf Deep-Link-Navigierbarkeit
- Permissions: `contents: read`

**Typische Laufzeit:** ~4 Minuten

---

### 8. `unit-tests.yml` — Frontend Unit Tests (Vitest)

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
- Permissions: `contents: read`

**Typische Laufzeit:** ~2 Minuten

---

### 9. `weekly-download-report.yml` — APK Download-Report

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
- Secrets: `KIROBI_TELEGRAM_BOT_TOKEN`, Chat-ID Fallback: `1066082496`

**Typische Laufzeit:** ~1 Minute

---

## WORKFLOW_COUNT Tracking

### Aktueller Stand: 9 Workflows (2026-05-24, OPE-301)

| Datei | Zählt |
|---|---|
| `build-release-apk.yml` | ✅ |
| `ci.yml` | ✅ |
| `e2e-keyboard-nav.yml` | ✅ |
| `integration-tests.yml` | ✅ |
| `lint-frontend.yml` | ✅ |
| `lint-workflows.yml` | ✅ |
| `story-nav-e2e.yml` | ✅ |
| `unit-tests.yml` | ✅ |
| `weekly-download-report.yml` | ✅ |
| **Gesamt** | **9** |

### Änderungshistorie

| Version | Count | Änderung | OPE |
|---|---|---|---|
| 2026-05-21 | 6 | Basis: ci, lint-workflows, story-nav-e2e, weekly-download-report, build-release-apk, e2e-keyboard-nav | — |
| 2026-05-22 | 7 | +unit-tests.yml | OPE-244 |
| 2026-05-22 | 8 | +integration-tests.yml, WORKFLOW_COUNT_REF=8 | OPE-248 |
| 2026-05-24 | 9 | +lint-frontend.yml, WORKFLOW_COUNT_REF=9 | OPE-301 |

---

## Quick-Reference: Lokale Debugging-Befehle

```bash
# Workflow lokal linten
actionlint .github/workflows/DATEI.yml

# yamllint lokal
yamllint -d '{extends: relaxed, rules: {line-length: {max: 160}}}' .github/workflows/*.yml

# shellcheck lokal
shellcheck -S warning scripts/*.sh

# Frontend Unit-Tests lokal (Vitest)
cd frontend && npx vitest run

# E2E lokal
cd tests/e2e && pytest test_story_nav_e2e.py -v

# Workflow-Anzahl lokal prüfen
find .github/workflows -maxdepth 1 -name "*.yml" | wc -l
```

## Nächste Schritte

- Bei neuen Workflows: `WORKFLOW_COUNT_REF` in `lint-workflows.yml` manuell aktualisieren + Tabelle in diesem Dokument ergänzen
- Bei shellcheck-Findings: `actionlint .github/workflows/DATEI.yml` lokal ausführen
- Bei Dependabot-Alerts: `ci.yml` Workflow-Logs + GitHub Security-Tab prüfen
