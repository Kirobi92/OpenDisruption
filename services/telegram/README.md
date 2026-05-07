---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# Service: telegram

Telegram-Bot als Bedienoberfläche für das Kirobi-System. Ermöglicht Sven den Zugriff auf System-Status, Supervisor-Tasks und Kirobi-Chat direkt aus Telegram heraus.

## Dateien

- `main.py` — FastAPI-Anwendung mit Bot-Logik, Webhook/Polling-Handler, Inline-Keyboards und Datenbankzugriff
- `requirements.txt` — Python-Abhängigkeiten
- `Dockerfile` — Container-Definition

## Unterordner

- `keycodi/` — Erweitertes KeyCodi-Modul mit separaten Modulen für Konfiguration (`config.py`), Datenbank (`db.py`), LLM-Anbindung (`llm.py`), Menüs (`menus.py`), Benachrichtigungen (`notify.py`), parallele Verarbeitung (`parallel.py`), Cron-Jobs (`cron.py`) und Telegram-API (`tg.py`)

## Konfiguration (Env-Variablen)

| Variable | Beschreibung |
|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Bot-Token von @BotFather |
| `TELEGRAM_ALLOWED_USER_IDS` | Kommagetrennte Telegram-User-IDs (Whitelist) |
| `TELEGRAM_WEBHOOK_HOST` | Webhook-URL (leer = Long-Polling) |
| `TELEGRAM_NOTIFY_CHANNEL_ID` | Kanal für Startup-Benachrichtigungen |
| `KIROBI_API_URL` | URL des API-Service (Standard: `http://api:8000`) |
| `KIROBI_BOT_USER` | Login-Name für JWT-Authentifizierung |
| `KIROBI_BOT_PASSWORD` | Passwort für JWT-Authentifizierung |

## Endpunkte

- `GET /health` — Liveness-Check
- `GET /ready` — Readiness mit Konfigurations-Status
- `GET /telegram/status` — Bot-Verbindungsstatus via Telegram API
- `POST /telegram/webhook` — Webhook-Empfänger

## Port

`8005` (konfigurierbar via `TELEGRAM_SERVICE_PORT`)
