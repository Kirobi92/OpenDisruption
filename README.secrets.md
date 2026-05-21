# README.secrets.md — GitHub Repository Secrets Audit

**Erstellt:** 2026-05-21  
**Erstellt von:** Kirobi CEO Runner (OPE-228)  
**Repo:** Kirobi APK / OpenDisruption  
**Zweck:** Dokumentation aller GitHub Repository Secrets — Name, Zweck, Rotation-Intervall, Zugriffsberechtigte

---

## Repository Secrets

| Secret Name | Zweck | Verwendet in | Rotation-Intervall | Wer hat Zugriff |
|---|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API Token — zum Senden von CI-Notifications (Lint-Fehler, E2E-Ergebnisse, Audit-Alerts) | `lint-workflows.yml`, `story-nav-e2e.yml`, `nightly-audit.yml`, `weekly-download-report.yml` | Empfehlung: alle 90 Tage | Sven Darusi (Repo-Owner) |
| `TELEGRAM_CHAT_ID` | Telegram Chat-ID für Direkt-Nachrichten an Sven (privater Chat) | `lint-workflows.yml`, `story-nav-e2e.yml`, `weekly-download-report.yml` | Bei Bot-Wechsel | Sven Darusi (Repo-Owner) |
| `TELEGRAM_NOTIFY_CHANNEL_ID` | Telegram Channel-ID für Kanal-Notifications (z. B. Ops-Alert-Channel) | `nightly-audit.yml` | Bei Channel-Änderung | Sven Darusi (Repo-Owner) |
| `GITHUB_TOKEN` | GitHub automatisch generiertes Deployment-Token — Zugriff auf GitHub API, Releases, Packages | `weekly-download-report.yml` | Automatisch pro Workflow-Run (GitHub-managed) | GitHub Actions (automatisch) |

---

## Repository Variables (vars.*)

| Variable Name | Zweck | Verwendet in | Standardwert | Wer setzt es |
|---|---|---|---|---|
| `KIROBI_LINT_NOTIFY_SUCCESS` | Steuert ob bei Lint-Erfolg eine Telegram-Notification gesendet wird (`true`/`false`) | `lint-workflows.yml` | `false` (ruhiger Betrieb) | Sven Darusi (Repo-Owner) |
| `KIROBI_STORY_E2E_NOTIFY_SUCCESS` | Steuert ob bei E2E-Erfolg eine Telegram-Notification gesendet wird (`true`/`false`) | `story-nav-e2e.yml` | `false` | Sven Darusi (Repo-Owner) |

---

## Secret-Kategorien & Klassifizierung

### 🔴 Kritisch — Sofortige Rotation bei Kompromittierung

| Secret | Risiko bei Kompromittierung | Sofortmaßnahme |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot kann zum Senden von Spam-/Phishing-Nachrichten missbraucht werden | Token auf @BotFather revoken, neues Token setzen |

### 🟡 Mittel — Rotation bei Anlass

| Secret | Risiko | Anlass für Rotation |
|---|---|---|
| `TELEGRAM_CHAT_ID` | Technisch kein Secret (öffentlich abrufbar), aber persönliche ID | Bei Bot-Wechsel |
| `TELEGRAM_NOTIFY_CHANNEL_ID` | Wie TELEGRAM_CHAT_ID — Channel-ID | Bei Channel-Umstrukturierung |

### 🟢 Niedrig — Automatisch verwaltet

| Secret | Verwaltung |
|---|---|
| `GITHUB_TOKEN` | Von GitHub automatisch pro Workflow-Run generiert und invalidiert. Keine manuelle Rotation nötig. |

---

## Nicht-Standard Secrets

### `secrets.token_hex` (install-test.yml)
- **Typ:** Python `secrets.token_hex(32)` — wird im Workflow dynamisch generiert
- **Zweck:** Ersatz für Placeholder-Werte (`AENDERE_*`, `changeme`) in `.env`-Dateien beim Install-Test
- **Ist KEIN GitHub-Secret:** Es ist ein Python `secrets`-Modul-Aufruf im Workflow-Script
- **Risiko:** Keins — ephemeral, nur für Test-Run verwendet

---

## Rotation-Checkliste

```
[ ] TELEGRAM_BOT_TOKEN — Letztes Rotation-Datum: unbekannt → Prüfen & ggf. rotieren
[ ] TELEGRAM_CHAT_ID — Prüfen ob noch korrekt (Sven: 1066082496)
[ ] TELEGRAM_NOTIFY_CHANNEL_ID — Prüfen ob Channel noch aktiv
[ ] GITHUB_TOKEN — Automatisch, kein Action nötig
```

---

## Wie Secrets rotieren

### TELEGRAM_BOT_TOKEN
1. Öffne Telegram → @BotFather
2. `/revoke` → Token für den Bot widerrufen
3. `/token` → Neuen Token generieren
4. GitHub Repo → Settings → Secrets and variables → Actions → `TELEGRAM_BOT_TOKEN` updaten

### TELEGRAM_CHAT_ID / TELEGRAM_NOTIFY_CHANNEL_ID
1. Chat/Channel ID via `@userinfobot` oder Telegram API abrufen
2. GitHub Repo → Settings → Secrets and variables → Actions → jeweiliges Secret updaten

---

## Compliance-Hinweise

- **GoBD:** Secrets dürfen nicht in Commit-History erscheinen → `.env`-Dateien in `.gitignore`
- **Prinzip:** Kein Secret wird in Workflow-Logs geloggt (GitHub maskiert registrierte Secrets automatisch)
- **Least-Privilege:** `GITHUB_TOKEN` Permissions in Workflows auf `contents: read` beschränken wo möglich
- **Audit-Trail:** Alle Secret-Änderungen werden im GitHub Audit Log festgehalten (Settings → Security → Audit log)

---

*Dieses Dokument ist WORKSPACE-klassifiziert (nicht SACRED/FAMILY_PRIVATE). Nicht in public Repos commiten wenn Secrets-Werte enthalten sind.*
