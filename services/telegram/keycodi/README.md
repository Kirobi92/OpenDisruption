---
zone: WORKSPACE
created_by: kirobi-docs
created_at: 2026-05-07
reviewed_by: pending
version: "1.0"
---

# services/telegram/keycodi

Telegram-Bot-Service für KeyCodi — ermöglicht die Steuerung und Benachrichtigung des OpenDisruption-Systems über Telegram.
Unterstützt Menü-Navigation, LLM-Anfragen, Cron-Jobs und parallele Task-Ausführung.

## Wichtige Dateien

- `main.py` — Einstiegspunkt: Bot-Initialisierung und Handler-Registrierung
- `config.py` — Konfiguration (Token, erlaubte User-IDs, Timeouts)
- `tg.py` — Telegram-API-Wrapper und Nachrichten-Hilfsfunktionen
- `llm.py` — LLM-Integration (Ollama-Anfragen aus dem Bot heraus)
- `menus.py` — Interaktive Inline-Keyboard-Menüs
- `notify.py` — Push-Benachrichtigungen an Sven
- `cron.py` — Geplante Aufgaben und Reminder
- `db.py` — Persistenz für Bot-Zustand und Gesprächshistorie
- `parallel.py` — Parallele Task-Ausführung für längere Operationen
