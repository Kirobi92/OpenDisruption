"""
kirobi_core/notify.py
Zone: WORKSPACE

Leichtgewichtiger Telegram-Notifier für KeyCodi-Status-Updates.
Sendet Nachrichten direkt via Telegram Bot API — kein laufender Service nötig.

Usage:
    from kirobi_core.notify import notify, notify_task_done, notify_task_start

    notify("✅ Qdrant-Collections initialisiert")
    notify_task_start("P0.1", "Docker Compose erweitern")
    notify_task_done("P0.1", "Docker Compose erweitern", success=True)
"""
from __future__ import annotations

import os
import urllib.request
import urllib.parse
import urllib.error
import json
import logging
from datetime import datetime

log = logging.getLogger("kirobi.notify")

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
# Bevorzuge erste User-ID (direkte DM), Channel-ID als Fallback
_CHAT_ID = (
    os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")[0].strip()
    or os.getenv("TELEGRAM_NOTIFY_CHANNEL_ID", "").strip()
)
_ENABLED = bool(_BOT_TOKEN and _CHAT_ID)


def _send_raw(text: str) -> bool:
    """Sendet eine Nachricht via Telegram Bot API (sync, stdlib-only)."""
    if not _ENABLED:
        log.debug("Telegram nicht konfiguriert — Nachricht nur geloggt: %s", text[:80])
        return False
    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": _CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return bool(data.get("ok"))
    except urllib.error.HTTPError as exc:
        log.warning("Telegram HTTP-Fehler %s: %s", exc.code, exc.read()[:200])
        return False
    except Exception as exc:
        log.warning("Telegram-Fehler: %s", exc)
        return False


def notify(message: str, *, emoji: str = "🤖") -> bool:
    """Sendet eine einfache Status-Nachricht."""
    ts = datetime.now().strftime("%H:%M:%S")
    text = f"{emoji} <b>KeyCodi</b> <code>{ts}</code>\n\n{message}"
    ok = _send_raw(text)
    if not ok:
        log.info("[NOTIFY] %s", message)
    return ok


def notify_task_start(task_id: str, title: str) -> bool:
    """Benachrichtigt über den Start einer Aufgabe."""
    return notify(
        f"▶️ <b>Starte:</b> {title}\n<code>{task_id}</code>",
        emoji="🔧",
    )


def notify_task_done(task_id: str, title: str, *, success: bool = True, detail: str = "") -> bool:
    """Benachrichtigt über den Abschluss einer Aufgabe."""
    icon = "✅" if success else "❌"
    status = "Erledigt" if success else "Fehlgeschlagen"
    msg = f"{icon} <b>{status}:</b> {title}\n<code>{task_id}</code>"
    if detail:
        msg += f"\n\n<i>{detail[:300]}</i>"
    return notify(msg, emoji=icon)


def notify_section(title: str, items: list[str]) -> bool:
    """Sendet eine strukturierte Zusammenfassung."""
    lines = [f"📋 <b>{title}</b>\n"]
    for item in items:
        lines.append(f"  {item}")
    return notify("\n".join(lines), emoji="📋")


def notify_upgrade_plan(plan: dict[str, list[str]]) -> bool:
    """Sendet den Upgrade-Plan als strukturierte Nachricht."""
    lines = ["🚀 <b>KeyCodi Upgrade-Plan</b>\n"]
    for phase, tasks in plan.items():
        lines.append(f"\n<b>{phase}</b>")
        for task in tasks:
            lines.append(f"  • {task}")
    return notify("\n".join(lines), emoji="🚀")


__all__ = [
    "notify",
    "notify_task_start",
    "notify_task_done",
    "notify_section",
    "notify_upgrade_plan",
]
