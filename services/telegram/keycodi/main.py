"""
services/telegram/keycodi/main.py
KeyCodi Telegram Bot v3 — FastAPI-Einstiegspunkt

Zone: WORKSPACE
Zweck: Orchestriert alle keycodi/-Module zu einem vollständigen Telegram-Bot.
       Unterstützt Webhook- und Long-Polling-Modus, State-Machine für
       Sitzungen, Auth-Guard, Cron-Jobs und Health-Endpoints.

Architektur:
  config   → Zentrale Konfiguration (Env-Vars)
  tg       → Telegram API Wrapper (send, edit_msg, answer_cb, set_commands)
  menus    → Screen-Builder + Inline-Keyboards
  db       → Postgres-Zugriff (Tasks, Events, Entscheidungen)
  llm      → Ollama-Anbindung (Chat, Parallel-Requests)
  cron     → Hintergrund-Jobs (Status-Report, Failure-Check, Decision-Remind)
  parallel → Parallele Ausführung (nicht direkt importiert, via llm genutzt)
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request

from .config import (
    ALLOWED_USER_IDS,
    BOT_TOKEN,
    KIROBI_TELEGRAM_PROGRESS_INTERVAL_SEC,
    KIROBI_API_URL,
    KIROBI_AUTH_URL,
    KIROBI_BOT_PASS,
    KIROBI_BOT_USER,
    NOTIFY_CHANNEL_ID,
    NOTIFY_ON_START,
    PORT,
    TELEGRAM_API,
    VOICE_SERVICE_URL,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
)
from . import db, cron
from .responder import build_keycodi_response_with_context
from .tg import (
    answer_cb,
    download_file,
    edit_msg,
    send,
    send_audio,
    set_chat_menu_commands,
    set_commands,
    set_descriptions,
)
from .menus import (
    kb_cancel,
    screen_agents,
    screen_decision_detail,
    screen_decisions,
    screen_events,
    screen_hardware,
    screen_home,
    screen_status,
    screen_surfaces,
    screen_task_detail,
    screen_tasks,
    screen_vault,
    screen_workbench,
)

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("keycodi.main")

# ─── Laufzeit-State ──────────────────────────────────────────────────────────

# user_id → {"state": str, "task_name": str, "decision_id": str}
_user_state: dict[int, dict] = {}

# user_id → conversation_id (Kirobi-API)
_conversation_by_user: dict[int, str] = {}

# user_id → letzte Chat-Turns fuer lokalen KeyCodi-Kontext
_chat_history_by_user: dict[int, list[tuple[str, str]]] = {}

# user_id → aktiver Chat-Modus ("keycodi" | "copilot")
_chat_mode_by_user: dict[int, str] = {}

# Gecachter JWT-Token für Kirobi-API
_api_token_cache: Optional[str] = None

# Aktiver Cron-Task (asyncio.Task)
_cron_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _html(value: object) -> str:
    """Escaped einen Wert für HTML-Ausgabe in Telegram."""
    return escape(str(value), quote=False)


def _message_id_from(result: dict) -> Optional[int]:
    """Extrahiert die message_id aus einer Telegram-API-Antwort."""
    payload = result.get("result")
    if isinstance(payload, dict):
        message_id = payload.get("message_id")
        if isinstance(message_id, int):
            return message_id
    return None


def _append_chat_turn(user_id: int, role: str, text: str, *, limit: int = 8) -> None:
    """Speichert die letzten Chat-Turns fuer den lokalen KeyCodi-Kontext."""
    history = _chat_history_by_user.setdefault(user_id, [])
    history.append((role, " ".join(text.split())))
    if len(history) > limit:
        del history[:-limit]


def _chat_context_for(user_id: int) -> str:
    """Rendert den letzten Chatverlauf kompakt fuer KeyCodi."""
    history = _chat_history_by_user.get(user_id, [])
    if not history:
        return ""
    lines: list[str] = []
    for role, text in history[-6:]:
        label = "Sven" if role == "user" else "Agent"
        lines.append(f"{label}: {text}")
    return "\n".join(lines)


def _response_title(source: str) -> str:
    """Human-readable Label fuer die aktuelle Antwortquelle."""
    if source in {"keycodi_local", "hermes_reasoner"}:
        return "KeyCodi"
    if source == "copilot_cloud":
        return "Copilot"
    if source == "local_keycodi_plan":
        return "KeyCodi Fallback"
    return "KeyCodi"


def _chat_mode_for(user_id: int) -> str:
    """Gibt den aktiven Chat-Modus zurück."""
    return _chat_mode_by_user.get(user_id, "keycodi")


def _status_text(step: int) -> str:
    """Statusmeldung fuer lange Telegram-Anfragen."""
    minute_word = "Minute" if step == 1 else "Minuten"
    return (
        "⏳ <b>KeyCodi arbeitet noch...</b>\n\n"
        f"Zwischenstand: {step} {minute_word} in Bearbeitung.\n"
        "Ich prüfe weiter die Anfrage und melde mich mit dem Ergebnis."
    )


async def _progress_reporter(chat_id: int, message_id: int, stop_event: asyncio.Event) -> None:
    """Aktualisiert die sichtbare Telegram-Statusmeldung periodisch."""
    step = 0
    while True:
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=max(1, KIROBI_TELEGRAM_PROGRESS_INTERVAL_SEC),
            )
            return
        except asyncio.TimeoutError:
            step += 1
            await edit_msg(chat_id, message_id, _status_text(step))


def _is_authorized(user_id: int) -> bool:
    """Prüft ob ein User in der Allowlist steht."""
    if not ALLOWED_USER_IDS:
        log.warning("TELEGRAM_ALLOWED_USER_IDS leer — alle Anfragen abgelehnt")
        return False
    return user_id in ALLOWED_USER_IDS


def _config_state() -> dict:
    """Gibt den aktuellen Konfigurationsstatus zurück."""
    return {
        "bot_token_configured": bool(BOT_TOKEN),
        "allowed_users_configured": bool(ALLOWED_USER_IDS),
        "notify_channel_configured": bool(NOTIFY_CHANNEL_ID),
        "notify_on_start": bool(NOTIFY_ON_START),
        "webhook_configured": bool(WEBHOOK_HOST),
        "api_token_configured": bool(_api_token_cache),
        "api_login_configured": bool(KIROBI_BOT_USER and KIROBI_BOT_PASS),
        "mode": "webhook" if WEBHOOK_HOST else "long-polling",
    }


# ─── Kirobi API Auth ─────────────────────────────────────────────────────────

async def _get_api_token(force_refresh: bool = False) -> Optional[str]:
    """Holt oder erneuert den JWT-Token für die Kirobi-API."""
    global _api_token_cache
    if _api_token_cache and not force_refresh:
        return _api_token_cache
    if not (KIROBI_BOT_USER and KIROBI_BOT_PASS):
        log.warning("Kirobi API-Login nicht konfiguriert (KIROBI_BOT_USER/PASS fehlen)")
        return _api_token_cache
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{KIROBI_AUTH_URL}/token",
                data={"username": KIROBI_BOT_USER, "password": KIROBI_BOT_PASS},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception as exc:
        log.warning("Auth-Service nicht erreichbar: %s", exc)
        return _api_token_cache
    if response.status_code != 200:
        log.warning("JWT-Login fehlgeschlagen: status=%s", response.status_code)
        return _api_token_cache
    try:
        token = response.json().get("access_token")
    except ValueError:
        return _api_token_cache
    if token:
        _api_token_cache = token
        log.info("JWT-Login für Telegram-Service erfolgreich")
    return _api_token_cache


def _api_headers() -> dict:
    """Gibt Authorization-Header zurück, falls Token vorhanden."""
    return {"Authorization": f"Bearer {_api_token_cache}"} if _api_token_cache else {}


async def _api_post(client: httpx.AsyncClient, path: str, payload: dict) -> httpx.Response:
    """POST an Kirobi-API mit automatischem Token-Refresh bei 401/403."""
    await _get_api_token()
    response = await client.post(
        f"{KIROBI_API_URL}{path}", json=payload, headers=_api_headers()
    )
    if response.status_code in (401, 403):
        await _get_api_token(force_refresh=True)
        response = await client.post(
            f"{KIROBI_API_URL}{path}", json=payload, headers=_api_headers()
        )
    return response


async def _ensure_conversation(
    client: httpx.AsyncClient, user_id: int, title_seed: str
) -> tuple[Optional[str], Optional[str]]:
    """Stellt sicher, dass eine API-Sitzung für den User existiert."""
    if user_id in _conversation_by_user:
        return _conversation_by_user[user_id], None
    response = await _api_post(
        client,
        "/conversations",
        {"title": f"Telegram: {title_seed[:40]}", "zone": "WORKSPACE"},
    )
    if response.status_code != 201:
        return None, f"Konversation konnte nicht erstellt werden ({response.status_code})"
    try:
        conversation_id = response.json().get("id")
    except ValueError:
        return None, "Ungültige API-Antwort beim Erstellen der Konversation"
    if not conversation_id:
        return None, "Konversation ohne ID erhalten"
    _conversation_by_user[user_id] = conversation_id
    return conversation_id, None


# ─── Chat mit lokalem KeyCodi / Kirobi-API-Fallback ──────────────────────────

async def _send_to_kirobi(chat_id: int, user_id: int, text: str) -> None:
    """Beantwortet Telegram-Chats zuerst ueber den lokalen KeyCodi-Pfad."""
    log.info("Chat-Nachricht von user_id=%s, Länge=%s", user_id, len(text))
    persona = _chat_mode_for(user_id)
    start_label = "Copilot" if persona == "copilot" else "KeyCodi"
    start_text = (
        "Ich prüfe deine Anfrage gegen den Repo-Kontext."
        if persona == "copilot"
        else "Ich analysiere deine Anfrage jetzt als KeyCodi — lokal, klar und ohne Placeholder."
    )
    pending = await send(
        chat_id,
        f"⌛ <b>{start_label} startet…</b>\n\n{start_text}",
    )
    pending_message_id = _message_id_from(pending)
    stop_progress = asyncio.Event()
    progress_task: Optional[asyncio.Task] = None
    if pending_message_id is not None:
        progress_task = asyncio.create_task(
            _progress_reporter(chat_id, pending_message_id, stop_progress)
        )

    try:
        local_response = await build_keycodi_response_with_context(
            text,
            context=_chat_context_for(user_id),
            persona=persona,
        )
        ai_response = local_response.content
        if len(ai_response) > 3800:
            ai_response = ai_response[:3800] + "\n\n<i>... (Antwort gekürzt)</i>"
        _append_chat_turn(user_id, "user", text)
        _append_chat_turn(user_id, "assistant", ai_response)
        stop_progress.set()
        if progress_task is not None:
            await progress_task
        if pending_message_id is not None:
            await edit_msg(
                chat_id,
                pending_message_id,
                f"✅ <b>{_response_title(local_response.source)}</b> hat geantwortet.",
            )
        from .menus import kb_back
        model_hint = (
            f"\n<i>Modell: {_html(local_response.model_used)}</i>"
            if local_response.model_used
            else ""
        )
        await send(
            chat_id,
            f"🧠 <b>{_response_title(local_response.source)}:</b>{model_hint}\n\n{_html(ai_response)}",
            kb_back(),
        )
        return
    except Exception as exc:
        log.warning("Lokaler KeyCodi-Antwortpfad nicht verfügbar: %s", type(exc).__name__)
        stop_progress.set()
        if progress_task is not None:
            await progress_task
        if pending_message_id is not None:
            await edit_msg(
                chat_id,
                pending_message_id,
                "⚠️ <b>Lokaler Agent nicht verfügbar.</b>\n\nIch versuche jetzt den API-Fallback.",
            )

    if not await _get_api_token():
        await send(
            chat_id,
            "❌ <b>API-Login nicht bereit.</b>\n\n"
            "Setze <code>KIROBI_BOT_PASSWORD</code> oder <code>KIROBI_DEFAULT_PASSWORD</code> "
            "und nutze bei Passwortdrift <code>make reset-default-password</code>.",
            kb_cancel(),
        )
        return

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            conversation_id, error = await _ensure_conversation(client, user_id, text)
            if error or not conversation_id:
                await send(
                    chat_id,
                    f"❌ API-Fehler: {_html(error or 'Keine Konversation verfügbar')}",
                    kb_cancel(),
                )
                return

            response = await _api_post(
                client,
                f"/conversations/{conversation_id}/messages",
                {"content": text},
            )
            if response.status_code == 404:
                _conversation_by_user.pop(user_id, None)
            if response.status_code != 200:
                await send(
                    chat_id,
                    f"❌ API-Fehler beim Nachrichtenversand ({response.status_code})",
                    kb_cancel(),
                )
                return

            try:
                ai_response = response.json().get("content", "(Keine Antwort)")
            except ValueError:
                ai_response = "(Ungültige API-Antwort)"

            if len(ai_response) > 3800:
                ai_response = ai_response[:3800] + "\n\n<i>... (Antwort gekürzt)</i>"
            _append_chat_turn(user_id, "user", text)
            _append_chat_turn(user_id, "assistant", ai_response)
            if pending_message_id is not None:
                await edit_msg(chat_id, pending_message_id, "✅ <b>API-Fallback</b> hat geantwortet.")

            from .menus import kb_back
            await send(chat_id, f"🧠 <b>KeyCodi API-Fallback:</b>\n\n{_html(ai_response)}", kb_back())

    except Exception as exc:
        log.error("Chat-Fehler: %s", exc)
        await send(chat_id, f"❌ Fehler: {_html(exc)}", kb_cancel())


async def _transcribe_telegram_audio(audio_path: str | Path, *, language: str = "de") -> str:
    """Gibt die Transkription einer Telegram-Audiodatei zurück."""
    async with httpx.AsyncClient(timeout=180) as client:
        with open(audio_path, "rb") as handle:
            files = {"audio_file": (Path(audio_path).name, handle, "application/octet-stream")}
            response = await client.post(
                f"{VOICE_SERVICE_URL}/stt/transcribe",
                files=files,
                data={"language": language},
            )
    response.raise_for_status()
    data = response.json()
    return str(data.get("text", "")).strip()


async def _synthesize_telegram_audio(text: str, *, language: str = "de") -> Path:
    """Erzeugt eine Audiodatei aus Text über den lokalen Voice-Service."""
    async with httpx.AsyncClient(timeout=180) as client:
        response = await client.post(
            f"{VOICE_SERVICE_URL}/tts/synthesize",
            json={"text": text, "language": language},
        )
        response.raise_for_status()
        data = response.json()
        audio_url = data.get("audio_url")
        if not audio_url:
            raise RuntimeError("Voice-Service lieferte keine audio_url")
        audio_response = await client.get(f"{VOICE_SERVICE_URL}{audio_url}")
        audio_response.raise_for_status()

    temp = tempfile.NamedTemporaryFile(prefix="telegram_tts_", suffix=".wav", delete=False)
    try:
        temp.write(audio_response.content)
        temp.flush()
    finally:
        temp.close()
    return Path(temp.name)


async def _handle_voice_message(chat_id: int, user_id: int, message: dict) -> None:
    """Verarbeitet Telegram-Sprachnachrichten und antwortet per Audio."""
    voice = message.get("voice") or message.get("audio")
    if not isinstance(voice, dict):
        await send(chat_id, "❌ Keine gültige Sprachnachricht erkannt.", kb_cancel())
        return

    file_id = voice.get("file_id")
    if not isinstance(file_id, str) or not file_id:
        await send(chat_id, "❌ Telegram hat keine Datei-ID für die Sprachnachricht geliefert.", kb_cancel())
        return

    pending = await send(
        chat_id,
        "🎙️ <b>KeyCodi verarbeitet deine Sprachnachricht…</b>\n\nIch lade das Audio, transkribiere es lokal und antworte dir gleich mit Stimme.",
    )
    pending_message_id = _message_id_from(pending)
    stop_progress = asyncio.Event()
    progress_task: Optional[asyncio.Task] = None
    if pending_message_id is not None:
        progress_task = asyncio.create_task(
            _progress_reporter(chat_id, pending_message_id, stop_progress)
        )

    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    try:
        suffix = ".ogg" if message.get("voice") else ".audio"
        temp_input = tempfile.NamedTemporaryFile(prefix="telegram_voice_", suffix=suffix, delete=False)
        input_path = Path(temp_input.name)
        temp_input.close()
        await download_file(file_id, input_path)

        transcript = await _transcribe_telegram_audio(input_path)
        if not transcript:
            raise RuntimeError("Transkription war leer")

        _append_chat_turn(user_id, "user", transcript)
        response = await build_keycodi_response_with_context(
            transcript,
            context=_chat_context_for(user_id),
            timeout=90.0,
        )
        ai_response = response.content.strip()
        if not ai_response:
            raise RuntimeError("KeyCodi hat keine Antwort geliefert")

        _append_chat_turn(user_id, "assistant", ai_response)
        output_path = await _synthesize_telegram_audio(ai_response)

        stop_progress.set()
        if progress_task is not None:
            await progress_task
        if pending_message_id is not None:
            await edit_msg(chat_id, pending_message_id, "✅ <b>KeyCodi Voice-Antwort ist bereit.</b>")

        await send(
            chat_id,
            "📝 <b>Transkription</b>\n\n"
            f"{_html(transcript[:1500])}"
            + ("\n\n<i>... gekürzt</i>" if len(transcript) > 1500 else ""),
        )
        await send_audio(
            chat_id,
            output_path,
            caption="🧠 KeyCodi Voice Reply",
        )
    except Exception as exc:
        stop_progress.set()
        if progress_task is not None:
            await progress_task
        if pending_message_id is not None:
            await edit_msg(
                chat_id,
                pending_message_id,
                "⚠️ <b>Voice-Verarbeitung fehlgeschlagen.</b>\n\nIch falle auf Text zurück.",
            )
        log.error("Voice-Fehler: %s", exc)
        await send(chat_id, f"❌ Voice-Fehler: {_html(exc)}", kb_cancel())
    finally:
        for path in (input_path, output_path):
            if path and path.exists():
                try:
                    os.remove(path)
                except OSError:
                    pass


# ─── System-Screen ───────────────────────────────────────────────────────────

async def _screen_system(user_name: str) -> tuple[str, dict]:
    """Zeigt den System-Screen mit API-Status und Bot-Konfiguration."""
    from .menus import kb_system
    return "🔧 <b>System</b>\n\nWähle einen Check:", kb_system()


async def _screen_sys_api() -> tuple[str, dict]:
    """Prüft den API-Token-Status."""
    from .menus import kb_back
    token = await _get_api_token(force_refresh=True)
    status = "✅ bereit" if token else "❌ nicht bereit"
    text = (
        f"🔐 <b>API-Status</b>\n\n"
        f"JWT-Token: <code>{status}</code>\n"
        f"Auth-URL: <code>{_html(KIROBI_AUTH_URL)}</code>\n"
        f"API-URL: <code>{_html(KIROBI_API_URL)}</code>"
    )
    return text, kb_back("m:system")


async def _screen_sys_bot() -> tuple[str, dict]:
    """Zeigt Bot-Informationen via Telegram getMe."""
    from .menus import kb_back
    from .tg import tg as _tg
    data = await _tg("getMe")
    bot = data.get("result", {}) if data.get("ok") else {}
    text = (
        "🤖 <b>Bot-Info</b>\n\n"
        f"Name: <code>{_html(bot.get('first_name', '?'))}</code>\n"
        f"Username: <code>@{_html(bot.get('username', '?'))}</code>\n"
        f"ID: <code>{_html(bot.get('id', '?'))}</code>\n"
        f"Modus: <code>{'webhook' if WEBHOOK_HOST else 'long-polling'}</code>"
    )
    return text, kb_back("m:system")


async def _screen_sys_config() -> tuple[str, dict]:
    """Zeigt die aktuelle Konfiguration (ohne Secrets)."""
    from .menus import kb_back
    cfg = _config_state()
    lines = ["📋 <b>Konfiguration</b>\n"]
    for key, val in cfg.items():
        icon = "✅" if val else "❌"
        lines.append(f"  {icon} <code>{_html(key)}</code>: <b>{_html(val)}</b>")
    return "\n".join(lines), kb_back("m:system")


# ─── Vault-Aktionen ──────────────────────────────────────────────────────────

async def _handle_vault_action(chat_id: int, user_id: int, action: str) -> None:
    """Verarbeitet Vault-Aktionen (daily, moc, read_prompt)."""
    from .menus import kb_back
    if action == "daily":
        await send(
            chat_id,
            "📅 <b>Daily Note</b>\n\nDie Daily-Note-Funktion ist über den Obsidian-Agenten verfügbar.\n"
            "Starte den Agenten via <code>/tasks</code> oder direkt im Vault.",
            kb_back("m:vault"),
        )
    elif action == "moc":
        await send(
            chat_id,
            "🗺 <b>MOC generieren</b>\n\nDer Obsidian-Agent generiert das MOC automatisch.\n"
            "Erstelle einen Task mit dem Agenten 'obsidian'.",
            kb_back("m:vault"),
        )
    elif action == "read_prompt":
        _user_state[user_id] = {"state": "awaiting_vault_note"}
        await send(
            chat_id,
            "📄 <b>Note lesen</b>\n\nGib den Namen oder Pfad der Note ein:",
            kb_cancel(),
        )
    else:
        await send(chat_id, "❓ Unbekannte Vault-Aktion.", kb_back("m:vault"))


# ─── Callback-Handler ────────────────────────────────────────────────────────

async def _handle_callback(callback_query: dict) -> None:
    """Verarbeitet alle Inline-Keyboard-Callbacks."""
    cb_id: str = callback_query["id"]
    message: dict = callback_query.get("message", {})
    chat_id: Optional[int] = message.get("chat", {}).get("id")
    message_id: Optional[int] = message.get("message_id")
    user: dict = callback_query.get("from", {})
    user_id: int = user.get("id", 0)
    user_name: str = user.get("first_name") or user.get("username") or "Unbekannt"
    data: str = callback_query.get("data", "")

    # Sofort bestätigen — verhindert "Uhr"-Animation in Telegram
    await answer_cb(cb_id)

    if not chat_id or not message_id:
        return

    # Auth-Guard
    if not _is_authorized(user_id):
        await answer_cb(cb_id, "⛔ Kein Zugriff", alert=True)
        return

    text: str = ""
    keyboard: dict = {}

    # ── Hauptmenü-Navigation ─────────────────────────────────────────────────
    if data == "m:home":
        text, keyboard = await screen_home(user_name)

    elif data == "m:status":
        text, keyboard = await screen_status()

    elif data == "m:tasks":
        text, keyboard = await screen_tasks()

    elif data == "m:surfaces":
        text, keyboard = await screen_surfaces()

    elif data == "m:workbench":
        text, keyboard = await screen_workbench()

    elif data == "m:agents":
        text, keyboard = await screen_agents()

    elif data == "m:vault":
        text, keyboard = await screen_vault()

    elif data == "m:events":
        text, keyboard = await screen_events()

    elif data == "m:decisions":
        text, keyboard = await screen_decisions()

    elif data == "m:hardware":
        text, keyboard = await screen_hardware()

    elif data == "m:system":
        text, keyboard = await _screen_system(user_name)

    elif data == "m:chat":
        _chat_mode_by_user[user_id] = "keycodi"
        _user_state[user_id] = {"state": "chatting"}
        text = "💬 <b>KeyCodi ist bereit.</b>\n\nSchreib einfach los. /new startet eine neue Sitzung."
        keyboard = kb_cancel()

    elif data == "m:copilot":
        _chat_mode_by_user[user_id] = "copilot"
        _user_state[user_id] = {"state": "chatting"}
        text = (
            "🤝 <b>Copilot ist bereit.</b>\n\n"
            "Frag direkt zum Repo, zu Code, Tests, Services oder Architektur."
        )
        keyboard = kb_cancel()

    elif data == "m:reset_chat":
        _conversation_by_user.pop(user_id, None)
        _chat_history_by_user.pop(user_id, None)
        _user_state[user_id] = {"state": "chatting"}
        text = "♻️ <b>KeyCodi-Sitzung zurückgesetzt.</b>\n\nSchreib direkt deine nächste Anfrage."
        keyboard = kb_cancel()

    elif data == "m:add_task":
        _user_state[user_id] = {"state": "awaiting_task_name", "sofort": False}
        text = "➕ <b>Neuer Task</b>\n\nWie soll der Task heißen?"
        keyboard = kb_cancel()

    elif data == "m:add_sofort":
        _user_state[user_id] = {"state": "awaiting_task_name", "sofort": True}
        text = "🚨 <b>SOFORT-Task</b>\n\nWie soll der Task heißen?"
        keyboard = kb_cancel()

    # ── Task-Detail ──────────────────────────────────────────────────────────
    elif data.startswith("task:v:"):
        task_id = data[len("task:v:"):]
        text, keyboard = await screen_task_detail(task_id)

    # ── Agenten-Detail ───────────────────────────────────────────────────────
    elif data.startswith("agent:"):
        agent_name = data[len("agent:"):]
        text, keyboard = await screen_agents(agent_name)

    # ── Vault-Aktionen ───────────────────────────────────────────────────────
    elif data.startswith("vault:"):
        action = data[len("vault:"):]
        await _handle_vault_action(chat_id, user_id, action)
        return  # _handle_vault_action sendet selbst

    # ── Entscheidungs-Detail ─────────────────────────────────────────────────
    elif data.startswith("dec:v:"):
        decision_id = data[len("dec:v:"):]
        text, keyboard = await screen_decision_detail(decision_id)

    elif data.startswith("dec:ans:"):
        # Format: dec:ans:<decision_id>:<option_index>
        parts = data[len("dec:ans:"):].rsplit(":", 1)
        if len(parts) == 2:
            decision_id, option_idx_str = parts
            try:
                # Lade Entscheidung um Option-Text zu ermitteln
                pool = await db.get_pool()
                if pool:
                    import json as _json
                    async with pool.acquire() as conn:
                        row = await conn.fetchrow(
                            "SELECT question, options FROM keycodi_decisions WHERE id=$1",
                            decision_id,
                        )
                    if row:
                        options: list = _json.loads(row["options"]) if row["options"] else []
                        idx = int(option_idx_str)
                        answer = options[idx] if 0 <= idx < len(options) else f"Option {idx}"
                        await db.decision_answer(decision_id, answer)
                        await db.event_log(
                            "decision_answered",
                            f"Entscheidung '{row['question'][:60]}' beantwortet: {answer}",
                            "info",
                            {"decision_id": decision_id, "answer": answer, "user_id": user_id},
                        )
                        from .menus import kb_back
                        text = f"✅ <b>Antwort gespeichert:</b>\n\n{_html(answer)}"
                        keyboard = kb_back("m:decisions")
                    else:
                        from .menus import kb_back
                        text = "❌ Entscheidung nicht gefunden."
                        keyboard = kb_back("m:decisions")
                else:
                    from .menus import kb_back
                    text = "❌ DB nicht erreichbar."
                    keyboard = kb_back("m:decisions")
            except Exception as exc:
                log.error("dec:ans Fehler: %s", exc)
                from .menus import kb_back
                text = f"❌ Fehler: {_html(exc)}"
                keyboard = kb_back("m:decisions")
        else:
            from .menus import kb_back
            text = "❌ Ungültiges Antwort-Format."
            keyboard = kb_back("m:decisions")

    elif data.startswith("dec:free:"):
        decision_id = data[len("dec:free:"):]
        _user_state[user_id] = {"state": "awaiting_decision_answer", "decision_id": decision_id}
        text = "✍️ <b>Freitext-Antwort</b>\n\nGib deine Antwort ein:"
        keyboard = kb_cancel()

    # ── System-Checks ────────────────────────────────────────────────────────
    elif data == "sys:api":
        text, keyboard = await _screen_sys_api()

    elif data == "sys:bot":
        text, keyboard = await _screen_sys_bot()

    elif data == "sys:config":
        text, keyboard = await _screen_sys_config()

    # ── Fallback → Hauptmenü ─────────────────────────────────────────────────
    else:
        log.debug("Unbekannter callback_data: %s", data)
        text, keyboard = await screen_home(user_name)

    if text:
        await edit_msg(chat_id, message_id, text, keyboard)


# ─── Message-Handler ─────────────────────────────────────────────────────────

async def _handle_message(chat_id: int, user_id: int, text: str, user_name: str) -> None:
    """Verarbeitet eingehende Textnachrichten mit State-Machine."""
    if not _is_authorized(user_id):
        await send(chat_id, "⛔ Zugriff verweigert.")
        return

    stripped = text.strip()
    state_data = _user_state.get(user_id, {})
    state = state_data.get("state", "idle")

    # ── Slash-Commands haben Vorrang ─────────────────────────────────────────
    if stripped.startswith("/"):
        parts = stripped.split(None, 1)
        command = parts[0].lstrip("/").split("@")[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""
        await _handle_slash(chat_id, user_id, user_name, command, args)
        return

    # ── State-Machine ────────────────────────────────────────────────────────

    if state == "awaiting_task_name":
        sofort = state_data.get("sofort", False)
        _user_state[user_id] = {"state": "awaiting_task_desc", "task_name": stripped, "sofort": sofort}
        label = "🚨 SOFORT-Task" if sofort else "Task"
        await send(
            chat_id,
            f"✏️ <b>{label}:</b> {_html(stripped)}\n\nGib jetzt eine kurze Beschreibung ein.",
            kb_cancel(),
        )
        return

    if state == "awaiting_task_desc":
        task_name = state_data.get("task_name", "Telegram Task")
        sofort = state_data.get("sofort", False)
        _user_state[user_id] = {"state": "idle"}
        try:
            task_id = await db.task_add(
                name=task_name,
                description=stripped,
                priority="high" if sofort else "medium",
                sofort=sofort,
                source="telegram",
            )
            await db.event_log(
                "task_created",
                f"Task '{task_name}' via Telegram erstellt",
                "info",
                {"task_id": task_id, "sofort": sofort, "user_id": user_id},
            )
            sofort_badge = " 🚨 SOFORT" if sofort else ""
            from .menus import kb_back
            await send(
                chat_id,
                f"✅ <b>Task erstellt!{sofort_badge}</b>\n\n"
                f"📌 <b>{_html(task_name)}</b>\n"
                f"🆔 <code>{_html(task_id)}</code>",
                kb_back(),
            )
        except Exception as exc:
            log.error("Task-Erstellung fehlgeschlagen: %s", exc)
            from .menus import kb_back
            await send(chat_id, f"❌ Fehler beim Erstellen: {_html(exc)}", kb_back())
        return

    if state == "awaiting_decision_answer":
        decision_id = state_data.get("decision_id", "")
        _user_state[user_id] = {"state": "idle"}
        if decision_id:
            try:
                await db.decision_answer(decision_id, stripped)
                await db.event_log(
                    "decision_answered",
                    f"Entscheidung {decision_id} mit Freitext beantwortet",
                    "info",
                    {"decision_id": decision_id, "user_id": user_id},
                )
                from .menus import kb_back
                await send(
                    chat_id,
                    f"✅ <b>Antwort gespeichert.</b>\n\n{_html(stripped[:200])}",
                    kb_back("m:decisions"),
                )
            except Exception as exc:
                log.error("Decision-Antwort fehlgeschlagen: %s", exc)
                from .menus import kb_back
                await send(chat_id, f"❌ Fehler: {_html(exc)}", kb_back("m:decisions"))
        return

    if state == "awaiting_vault_note":
        _user_state[user_id] = {"state": "idle"}
        from .menus import kb_back
        await send(
            chat_id,
            f"📄 <b>Note-Anfrage:</b> <code>{_html(stripped)}</code>\n\n"
            "Der Obsidian-Agent wird die Note laden. Erstelle einen Task für den Agenten.",
            kb_back("m:vault"),
        )
        return

    # ── Chatting-State oder impliziter Chat ──────────────────────────────────
    _user_state[user_id] = {"state": "chatting"}
    await _send_to_kirobi(chat_id, user_id, stripped)


# ─── Slash-Command-Handler ───────────────────────────────────────────────────

async def _handle_slash(
    chat_id: int, user_id: int, user_name: str, command: str, args: str
) -> None:
    """Verarbeitet alle /slash-Befehle."""
    if command in ("start", "help"):
        _user_state[user_id] = {"state": "idle"}
        text, keyboard = await screen_home(user_name)
        await send(chat_id, text, keyboard)

    elif command == "status":
        text, keyboard = await screen_status()
        await send(chat_id, text, keyboard)

    elif command == "surfaces":
        text, keyboard = await screen_surfaces()
        await send(chat_id, text, keyboard)

    elif command == "tasks":
        text, keyboard = await screen_tasks()
        await send(chat_id, text, keyboard)

    elif command == "events":
        text, keyboard = await screen_events()
        await send(chat_id, text, keyboard)

    elif command == "chat":
        _chat_mode_by_user[user_id] = "keycodi"
        _user_state[user_id] = {"state": "chatting"}
        await send(
            chat_id,
            "💬 <b>KeyCodi ist bereit.</b>\n\nSchreib einfach los. /new startet eine neue Sitzung.",
            kb_cancel(),
        )

    elif command == "copilot":
        _chat_mode_by_user[user_id] = "copilot"
        _user_state[user_id] = {"state": "chatting"}
        await send(
            chat_id,
            "🤝 <b>Copilot ist bereit.</b>\n\nFrag direkt zum Repo, zu Code, Tests, Services oder Architektur.",
            kb_cancel(),
        )

    elif command in ("new", "reset"):
        _conversation_by_user.pop(user_id, None)
        _chat_history_by_user.pop(user_id, None)
        _user_state[user_id] = {"state": "chatting"}
        await send(
            chat_id,
            "✅ <b>Neue KeyCodi-Sitzung gestartet.</b>\n\nSchreib einfach los.",
            kb_cancel(),
        )

    elif command == "add":
        if args:
            # Kurzform: /add Task-Name | Beschreibung
            parts = args.split("|", 1)
            task_name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else task_name
            try:
                task_id = await db.task_add(
                    name=task_name,
                    description=description,
                    source="telegram",
                )
                from .menus import kb_back
                await send(
                    chat_id,
                    f"✅ Task <b>{_html(task_name)}</b> erstellt.\n🆔 <code>{_html(task_id)}</code>",
                    kb_back(),
                )
            except Exception as exc:
                log.error("Task-Erstellung via /add fehlgeschlagen: %s", exc)
                from .menus import kb_back
                await send(chat_id, f"❌ Fehler: {_html(exc)}", kb_back())
        else:
            _user_state[user_id] = {"state": "awaiting_task_name", "sofort": False}
            await send(
                chat_id,
                "➕ <b>Neuer Task</b>\n\nWie soll der Task heißen?",
                kb_cancel(),
            )

    else:
        # Unbekannter Command → Hauptmenü
        text, keyboard = await screen_home(user_name)
        await send(chat_id, text, keyboard)


# ─── Update-Dispatcher ───────────────────────────────────────────────────────

async def _process_update(update: dict) -> None:
    """Dispatcht ein Telegram-Update an den passenden Handler."""
    try:
        if "callback_query" in update:
            await _handle_callback(update["callback_query"])
            return

        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id: int = message["chat"]["id"]
        user: dict = message.get("from", {})
        user_id: int = user.get("id", 0)
        user_name: str = user.get("first_name") or user.get("username") or "Unbekannt"
        text: str = message.get("text", "").strip()

        if text:
            await _handle_message(chat_id, user_id, text, user_name)
            return

        if message.get("voice") or message.get("audio"):
            await _handle_voice_message(chat_id, user_id, message)

    except Exception as exc:
        log.error("Update-Verarbeitung fehlgeschlagen: %s", exc, exc_info=True)


# ─── Long-Polling ────────────────────────────────────────────────────────────

async def _polling_loop() -> None:
    """Long-Polling-Loop — läuft als asyncio.Task wenn kein Webhook konfiguriert."""
    log.info("Long-Polling gestartet")
    offset = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    f"{TELEGRAM_API}/getUpdates",
                    json={"offset": offset, "timeout": 30, "limit": 100},
                )
            try:
                data = response.json()
            except ValueError:
                data = {"ok": False}
            updates = data.get("result", []) if data.get("ok") else []
            for update in updates:
                offset = update["update_id"] + 1
                asyncio.create_task(_process_update(update))
        except asyncio.CancelledError:
            log.info("Long-Polling beendet")
            break
        except Exception as exc:
            log.error("Polling-Fehler: %s", exc)
            await asyncio.sleep(5)


# ─── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="KeyCodi Telegram Bot",
    version="3.0.0",
    description="KeyCodi — Telegram-Interface für das OpenDisruption-Ökosystem",
)


@app.get("/health")
async def health() -> dict:
    """Liveness-Probe — antwortet immer mit ok."""
    return {"status": "ok", "service": "keycodi-telegram", "version": "3.0"}


@app.get("/ready")
async def ready() -> dict:
    """Readiness-Probe — prüft Konfiguration und DB-Verbindung."""
    cfg = _config_state()
    pool = await db.get_pool()
    db_ok = pool is not None

    is_ready = bool(
        cfg["bot_token_configured"]
        and cfg["allowed_users_configured"]
        and db_ok
    )
    return {
        "status": "ready" if is_ready else "degraded",
        "service": "keycodi-telegram",
        "version": "3.0",
        "config": cfg,
        "db_connected": db_ok,
        "active_conversations": len(_conversation_by_user),
        "active_user_states": len(_user_state),
    }


@app.post(WEBHOOK_PATH)
async def webhook(request: Request) -> dict:
    """Empfängt Telegram-Updates via Webhook."""
    try:
        update = await request.json()
        asyncio.create_task(_process_update(update))
    except Exception as exc:
        log.error("Webhook-Fehler: %s", exc)
    return {"ok": True}


@app.on_event("startup")
async def startup() -> None:
    """Initialisiert alle Services beim App-Start."""
    global _cron_task

    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN fehlt — Bot inaktiv")
        return

    log.info(
        "KeyCodi Telegram-Bot v3 startet. Autorisierte User: %s",
        len(ALLOWED_USER_IDS),
    )

    # DB-Pool initialisieren
    pool = await db.get_pool()
    if pool is None:
        log.warning("DB-Pool konnte nicht initialisiert werden — Bot läuft ohne DB")
    else:
        log.info("DB-Pool bereit")

    # Bot-Commands setzen
    await set_commands([
        {"command": "start",    "description": "KeyCodi-Menü öffnen"},
        {"command": "status",   "description": "System-Status anzeigen"},
        {"command": "surfaces", "description": "Weboberflächen öffnen"},
        {"command": "tasks",    "description": "Aufgaben anzeigen"},
        {"command": "add",      "description": "Neue Aufgabe anlegen"},
        {"command": "chat",     "description": "Direkt mit KeyCodi chatten"},
        {"command": "copilot",  "description": "Direkt mit Copilot im Repo chatten"},
        {"command": "new",      "description": "Neue KeyCodi-Sitzung starten"},
        {"command": "events",   "description": "Letzte Ereignisse"},
        {"command": "help",     "description": "Hilfe anzeigen"},
    ])
    await set_descriptions(
        "KeyCodi steuert OpenDisruption lokal-first: Chat, Suche, Upload, Operator-Dashboard und Telegram-Menüs.",
        "OpenDisruption unterwegs bedienen",
    )
    await set_chat_menu_commands()

    # API-Token vorab holen
    await _get_api_token()

    # Webhook oder Long-Polling starten
    if WEBHOOK_HOST:
        webhook_url = f"{WEBHOOK_HOST.rstrip('/')}{WEBHOOK_PATH}"
        from .tg import tg as _tg
        result = await _tg("setWebhook", url=webhook_url, drop_pending_updates=True)
        log.info("Webhook gesetzt (%s): %s", webhook_url, result.get("ok"))
    else:
        asyncio.create_task(_polling_loop())
        log.info("Long-Polling-Task gestartet")

    # Cron-Jobs starten
    notify_ids: list[str | int] = []
    if NOTIFY_CHANNEL_ID:
        notify_ids.append(NOTIFY_CHANNEL_ID)
    # Alle autorisierten User als Cron-Empfänger
    notify_ids.extend(ALLOWED_USER_IDS)

    _cron_task = cron.start_cron(notify_ids)
    log.info("Cron-Jobs gestartet (Empfänger: %s)", len(notify_ids))

    # Startup-Benachrichtigung
    if NOTIFY_CHANNEL_ID and NOTIFY_ON_START:
        try:
            await send(
                NOTIFY_CHANNEL_ID,
                "🚀 <b>KeyCodi Telegram-Bot v3 gestartet</b>\n"
                f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                "Sende /start um das Menü zu öffnen.",
                log_failures=False,
            )
        except Exception as exc:
            log.warning("Startup-Notify fehlgeschlagen: %s", exc)

    await db.event_log(
        "bot_startup",
        "KeyCodi Telegram-Bot v3 gestartet",
        "info",
        {
            "mode": "webhook" if WEBHOOK_HOST else "long-polling",
            "allowed_users": len(ALLOWED_USER_IDS),
        },
    )


@app.on_event("shutdown")
async def shutdown() -> None:
    """Räumt beim App-Stop auf."""
    global _cron_task

    log.info("KeyCodi Telegram-Bot v3 fährt herunter")

    # Cron stoppen
    cron.stop_cron()
    if _cron_task and not _cron_task.done():
        _cron_task.cancel()
        try:
            await _cron_task
        except asyncio.CancelledError:
            pass
    _cron_task = None

    # Webhook entfernen (nur wenn Webhook-Modus aktiv)
    if BOT_TOKEN and WEBHOOK_HOST:
        try:
            from .tg import tg as _tg
            await _tg("deleteWebhook", drop_pending_updates=True)
            log.info("Webhook entfernt")
        except Exception as exc:
            log.warning("Webhook-Entfernung fehlgeschlagen: %s", exc)

    # DB-Pool schließen
    await db.close_pool()
    log.info("DB-Pool geschlossen")

    await db.event_log(
        "bot_shutdown",
        "KeyCodi Telegram-Bot v3 heruntergefahren",
        "info",
        {},
    )
