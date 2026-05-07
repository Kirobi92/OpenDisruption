"""
services/telegram/keycodi/notify.py
KeyCodi Status-Reporting via Telegram — direkte Benachrichtigungen ohne Bot-Loop.

Zone: WORKSPACE
Zweck: Ermöglicht KeyCodi und anderen Services, Status-Updates, Fortschritt
       und Fehler direkt an Sven via Telegram zu senden.

Verwendung (standalone, ohne laufenden Bot):
    from services.telegram.keycodi.notify import keycodi_notify
    await keycodi_notify("✅ Task abgeschlossen: Embeddings-Service deployed")

Oder als CLI:
    python3 -m services.telegram.keycodi.notify "Nachricht hier"
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

# .env laden (funktioniert auch außerhalb des Containers)
_env_path = Path(__file__).resolve().parents[3] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

log = logging.getLogger("keycodi.notify")

# ─── Konfiguration ───────────────────────────────────────────────────────────
_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
_CHAT_ID: str = (
    os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")[0]
    or os.getenv("TELEGRAM_NOTIFY_CHANNEL_ID", "")
).strip()
_TELEGRAM_API: str = f"https://api.telegram.org/bot{_BOT_TOKEN}"

# Emojis für verschiedene Status-Typen
_EMOJI = {
    "start":    "🚀",
    "done":     "✅",
    "error":    "❌",
    "warn":     "⚠️",
    "info":     "ℹ️",
    "progress": "⏳",
    "test":     "🧪",
    "deploy":   "🐳",
    "commit":   "📦",
    "plan":     "📋",
}


def _chunks(text: str, size: int = 3900) -> list[str]:
    """Teilt langen Text in Telegram-konforme Chunks."""
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


async def _send_raw(text: str, chat_id: Optional[str] = None) -> bool:
    """Sendet eine Nachricht direkt via Telegram Bot API."""
    target = chat_id or _CHAT_ID
    if not _BOT_TOKEN or not target:
        log.warning("Telegram nicht konfiguriert (BOT_TOKEN oder CHAT_ID fehlt)")
        return False

    url = f"{_TELEGRAM_API}/sendMessage"
    success = True
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in _chunks(text):
            try:
                r = await client.post(url, json={
                    "chat_id": target,
                    "text": chunk,
                    "parse_mode": "HTML",
                })
                data = r.json()
                if not data.get("ok"):
                    # Fallback ohne parse_mode
                    r2 = await client.post(url, json={
                        "chat_id": target,
                        "text": chunk,
                    })
                    data2 = r2.json()
                    if not data2.get("ok"):
                        log.warning("Telegram send fehlgeschlagen: %s", data2.get("description"))
                        success = False
            except Exception as exc:
                log.warning("Telegram send Exception: %s", exc)
                success = False
    return success


async def keycodi_notify(
    message: str,
    kind: str = "info",
    title: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Sendet eine formatierte Status-Nachricht an Sven via Telegram.

    Args:
        message: Die Nachricht (kann HTML enthalten)
        kind: Typ der Nachricht (start/done/error/warn/info/progress/test/deploy/commit/plan)
        title: Optionaler Titel (fett)
        chat_id: Optionale Chat-ID (überschreibt Default)

    Returns:
        True wenn erfolgreich gesendet
    """
    emoji = _EMOJI.get(kind, "ℹ️")
    ts = datetime.now().strftime("%H:%M:%S")

    parts = [f"{emoji} <b>[KeyCodi {ts}]</b>"]
    if title:
        parts.append(f"<b>{escape(title)}</b>")
    parts.append(message)

    text = "\n".join(parts)
    return await _send_raw(text, chat_id=chat_id)


async def keycodi_progress(
    current: int,
    total: int,
    task: str,
    detail: Optional[str] = None,
) -> bool:
    """Sendet einen Fortschritts-Bericht."""
    pct = int((current / total) * 100) if total > 0 else 0
    bar_filled = pct // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    text = (
        f"⏳ <b>[KeyCodi] Fortschritt {current}/{total} ({pct}%)</b>\n"
        f"<code>[{bar}]</code>\n"
        f"📌 {escape(task)}"
    )
    if detail:
        text += f"\n<i>{escape(detail)}</i>"

    return await _send_raw(text)


async def keycodi_task_done(task_name: str, details: Optional[str] = None) -> bool:
    """Meldet einen abgeschlossenen Task."""
    text = f"✅ <b>[KeyCodi] Task abgeschlossen</b>\n📌 <code>{escape(task_name)}</code>"
    if details:
        text += f"\n\n{escape(details)}"
    return await _send_raw(text)


async def keycodi_task_failed(task_name: str, error: str) -> bool:
    """Meldet einen fehlgeschlagenen Task."""
    text = (
        f"❌ <b>[KeyCodi] Task fehlgeschlagen</b>\n"
        f"📌 <code>{escape(task_name)}</code>\n"
        f"💥 <i>{escape(error[:500])}</i>"
    )
    return await _send_raw(text)


async def keycodi_mission_start(mission: str, tasks: list[str]) -> bool:
    """Meldet den Start einer Mission mit Aufgabenliste."""
    task_list = "\n".join(f"  • {escape(t)}" for t in tasks)
    text = (
        f"🚀 <b>[KeyCodi] Mission gestartet</b>\n"
        f"<b>{escape(mission)}</b>\n\n"
        f"<b>Aufgaben:</b>\n{task_list}"
    )
    return await _send_raw(text)


async def keycodi_mission_done(mission: str, summary: str) -> bool:
    """Meldet den Abschluss einer Mission."""
    text = (
        f"🎉 <b>[KeyCodi] Mission abgeschlossen!</b>\n"
        f"<b>{escape(mission)}</b>\n\n"
        f"{escape(summary)}"
    )
    return await _send_raw(text)


# ─── CLI-Modus ───────────────────────────────────────────────────────────────

def _cli() -> None:
    """CLI: python3 -m services.telegram.keycodi.notify 'Nachricht' [kind]"""
    if len(sys.argv) < 2:
        print("Verwendung: python3 notify.py 'Nachricht' [kind]")
        print(f"Kinds: {', '.join(_EMOJI.keys())}")
        sys.exit(1)

    msg = sys.argv[1]
    kind = sys.argv[2] if len(sys.argv) > 2 else "info"

    ok = asyncio.run(keycodi_notify(msg, kind=kind))
    if ok:
        print(f"✅ Nachricht gesendet an {_CHAT_ID}")
    else:
        print("❌ Senden fehlgeschlagen — Token/Chat-ID prüfen")
        sys.exit(1)


if __name__ == "__main__":
    _cli()
