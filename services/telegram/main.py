from __future__ import annotations

"""
Kirobi Telegram-Bot Service -- v2
Zone: WORKSPACE
Zweck: Telegram-Interface fuer Sven -> Kirobi-System (API, Supervisor, Status)
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from html import escape
from typing import Optional

import asyncpg
import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from kirobi_core.asyncpg_compat import ensure_asyncpg_compat

asyncpg = ensure_asyncpg_compat(asyncpg)

load_dotenv()

# --- Konfiguration ----------------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_IDS = {
    int(uid.strip())
    for uid in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
    if uid.strip().isdigit()
}
NOTIFY_CHANNEL_ID = os.getenv("TELEGRAM_NOTIFY_CHANNEL_ID", "").strip()
NOTIFY_ON_START = os.getenv("TELEGRAM_NOTIFY_ON_START", "false").strip().lower() in {"1", "true", "yes", "ja"}

KIROBI_API_URL = os.getenv("KIROBI_API_URL", "http://api:8000").rstrip("/")
KIROBI_AUTH_URL = os.getenv("KIROBI_AUTH_URL", os.getenv("AUTH_SERVICE_URL", "http://auth:8000")).rstrip("/")
KIROBI_API_TOKEN = os.getenv("KIROBI_API_TOKEN", "").strip()
KIROBI_BOT_USER = os.getenv("KIROBI_BOT_USER", "").strip() or os.getenv("KIROBI_DEFAULT_USER", "sven").strip()
KIROBI_BOT_PASS = os.getenv("KIROBI_BOT_PASSWORD", "").strip() or os.getenv("KIROBI_DEFAULT_PASSWORD", "").strip()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'kirobi')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'changeme')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'kirobi')}"
)

WEBHOOK_HOST = os.getenv("TELEGRAM_WEBHOOK_HOST", "").strip()
WEBHOOK_PATH = "/telegram/webhook"
PORT = int(os.getenv("TELEGRAM_SERVICE_PORT", "8005"))
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("kirobi.telegram")

# --- State ------------------------------------------------------------------

db_pool: Optional[asyncpg.Pool] = None
api_token_cache: Optional[str] = KIROBI_API_TOKEN or None
user_state: dict[int, dict] = {}
# (user_id, agent) -> conversation_id  — eigene Konversation pro Agent
conversation_by_user: dict[tuple[int, str], str] = {}
# user_id -> aktiv ausgewählter Agent
active_agent_by_user: dict[int, str] = {}

DEFAULT_AGENT = "kirobi"
AGENT_CATALOG: list[dict[str, str]] = [
    {"id": "kirobi",            "label": "🌌 Kirobi",          "desc": "Allround-Begleiter"},
    {"id": "keycodi",           "label": "🧭 KeyCodi",         "desc": "Master-Code-Orchestrator"},
    {"id": "hermes",            "label": "🪶 Hermes",          "desc": "Reasoning & Synthese"},
    {"id": "opencode",          "label": "🛠️ Opencode",        "desc": "Code-Workbench"},
    {"id": "researcher",        "label": "🔬 Researcher",      "desc": "Recherche tief & breit"},
    {"id": "strategist",        "label": "♟️ Strategist",      "desc": "Strategie & Entscheidungen"},
    {"id": "kirobi-architect",  "label": "🏛️ Architect",       "desc": "Architektur & Design"},
    {"id": "kirobi-coder",      "label": "👨‍💻 Coder",          "desc": "Implementierung"},
    {"id": "kirobi-frontend",   "label": "🎨 Frontend",        "desc": "UI & UX Code"},
    {"id": "kirobi-ops",        "label": "⚙️ Ops",             "desc": "Infra & Deployment"},
    {"id": "kirobi-docs",       "label": "📚 Docs",            "desc": "Dokumentation"},
    {"id": "kirobi-reviewer",   "label": "🔍 Reviewer",        "desc": "Code-Review"},
    {"id": "code-reviewer",     "label": "🧪 Code-Reviewer",   "desc": "Strenger PR-Review"},
    {"id": "security-auditor",  "label": "🛡️ Security",        "desc": "Threat-Modeling"},
    {"id": "test-engineer",     "label": "✅ Test-Engineer",    "desc": "Tests schreiben"},
]
AGENT_LOOKUP: dict[str, dict[str, str]] = {a["id"]: a for a in AGENT_CATALOG}


def _html(value: object) -> str:
    return escape(str(value), quote=False)


def _config_state() -> dict:
    return {
        "bot_token_configured": bool(BOT_TOKEN),
        "allowed_users_configured": bool(ALLOWED_USER_IDS),
        "notify_channel_configured": bool(NOTIFY_CHANNEL_ID),
        "notify_on_start": bool(NOTIFY_ON_START),
        "webhook_configured": bool(WEBHOOK_HOST),
        "api_token_configured": bool(KIROBI_API_TOKEN),
        "api_login_configured": bool(KIROBI_BOT_USER and KIROBI_BOT_PASS),
        "mode": "webhook" if WEBHOOK_HOST else "long-polling",
    }


def _response_json(response: httpx.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {"ok": False, "status_code": response.status_code}


def _message_chunks(text: str, size: int = 3900) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)] or [""]


def _supervisor_unavailable(exc: Exception) -> bool:
    return isinstance(exc, asyncpg.UndefinedTableError)


# --- Telegram API -----------------------------------------------------------

async def tg(method: str, *, log_failures: bool = True, **kwargs) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{TELEGRAM_API}/{method}", json=kwargs)
    data = _response_json(response)
    if log_failures and not data.get("ok"):
        log.warning("Telegram %s failed: %s", method, data.get("description", response.status_code))
    return data


async def send(
    chat_id: int | str,
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: str = "HTML",
    *,
    log_failures: bool = True,
) -> dict:
    result: dict = {"ok": False}
    for chunk in _message_chunks(text):
        payload = {"chat_id": chat_id, "text": chunk}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        result = await tg("sendMessage", log_failures=log_failures, **payload)
        if result.get("ok"):
            continue

        if parse_mode:
            fallback = {"chat_id": chat_id, "text": chunk}
            if reply_markup:
                fallback["reply_markup"] = reply_markup
            result = await tg("sendMessage", log_failures=log_failures, **fallback)
        if not result.get("ok"):
            return result
    return result


async def edit_msg(chat_id: int | str, message_id: int, text: str, reply_markup: Optional[dict] = None) -> dict:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    result = await tg("editMessageText", **payload)
    if not result.get("ok"):
        return await send(chat_id, text, reply_markup)
    return result


async def answer_callback(callback_query_id: str, text: str = "") -> dict:
    return await tg("answerCallbackQuery", callback_query_id=callback_query_id, text=text)


async def set_bot_commands() -> None:
    commands = [
        {"command": "start", "description": "Hauptmenue oeffnen"},
        {"command": "agents", "description": "Agent waehlen"},
        {"command": "agent", "description": "Agent setzen: /agent hermes"},
        {"command": "who", "description": "Aktuellen Agent zeigen"},
        {"command": "status", "description": "System-Status"},
        {"command": "tasks", "description": "Tasks anzeigen"},
        {"command": "add", "description": "Neuen Task anlegen"},
        {"command": "chat", "description": "Mit aktivem Agent chatten"},
        {"command": "new", "description": "Neue Konversation"},
        {"command": "events", "description": "Letzte Ereignisse"},
        {"command": "help", "description": "Hilfe"},
    ]
    result = await tg("setMyCommands", commands=commands)
    log.info("Bot-Commands gesetzt: %s", result.get("ok"))


# --- Auth / API -------------------------------------------------------------

async def get_api_token(force_refresh: bool = False) -> Optional[str]:
    global api_token_cache
    if api_token_cache and not force_refresh:
        return api_token_cache
    if not (KIROBI_BOT_USER and KIROBI_BOT_PASS):
        log.warning("Kirobi API login is not configured")
        return api_token_cache

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"{KIROBI_AUTH_URL}/token",
                data={"username": KIROBI_BOT_USER, "password": KIROBI_BOT_PASS},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception as exc:
        log.warning("Auth-Service nicht erreichbar: %s", exc)
        return api_token_cache

    if response.status_code != 200:
        log.warning("JWT-Login fehlgeschlagen: status=%s", response.status_code)
        return api_token_cache

    token = _response_json(response).get("access_token")
    if token:
        api_token_cache = token
        log.info("JWT-Login fuer Telegram-Service erfolgreich")
    return api_token_cache


def api_headers() -> dict:
    return {"Authorization": f"Bearer {api_token_cache}"} if api_token_cache else {}


async def _api_post(client: httpx.AsyncClient, path: str, payload: dict) -> httpx.Response:
    await get_api_token()
    response = await client.post(f"{KIROBI_API_URL}{path}", json=payload, headers=api_headers())
    if response.status_code in (401, 403):
        await get_api_token(force_refresh=True)
        response = await client.post(f"{KIROBI_API_URL}{path}", json=payload, headers=api_headers())
    return response


async def _ensure_conversation(client: httpx.AsyncClient, user_id: int, agent: str, title_seed: str) -> tuple[Optional[str], Optional[str]]:
    key = (user_id, agent)
    if key in conversation_by_user:
        return conversation_by_user[key], None

    label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
    response = await _api_post(
        client,
        "/conversations",
        {"title": f"TG {label}: {title_seed[:30]}", "zone": "WORKSPACE"},
    )
    if response.status_code != 201:
        return None, f"Konversation konnte nicht erstellt werden ({response.status_code})"

    conversation_id = _response_json(response).get("id")
    if not conversation_id:
        return None, "Konversation ohne ID erhalten"
    conversation_by_user[key] = conversation_id
    return conversation_id, None


async def send_to_kirobi(chat_id: int, user_id: int, text: str) -> None:
    agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
    label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
    log.info("Chat-Nachricht von user_id=%s agent=%s length=%s", user_id, agent, len(text))
    await send(chat_id, f"⌛ {label} denkt nach...")

    if not await get_api_token():
        await send(
            chat_id,
            "❌ <b>API-Login nicht bereit.</b>\n\n"
            "Setze <code>KIROBI_BOT_PASSWORD</code> oder <code>KIROBI_DEFAULT_PASSWORD</code> "
            "und nutze bei Passwortdrift <code>make reset-default-password</code>.",
            back_keyboard(),
        )
        return

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            conversation_id, error = await _ensure_conversation(client, user_id, agent, text)
            if error or not conversation_id:
                await send(chat_id, f"❌ API-Fehler: {_html(error or 'Keine Konversation verfuegbar')}", back_keyboard())
                return

            response = await _api_post(
                client,
                f"/conversations/{conversation_id}/messages",
                {"content": text, "agent": agent},
            )
            if response.status_code == 404:
                conversation_by_user.pop((user_id, agent), None)
            if response.status_code != 200:
                await send(chat_id, f"❌ API-Fehler beim Nachrichtenversand ({response.status_code})", back_keyboard())
                return

            payload = _response_json(response)
            ai_response = payload.get("content", "(Keine Antwort)")
            model_used = payload.get("model_used") or ""
            footer = f"\n\n<i>— {label}{' · <code>' + _html(model_used) + '</code>' if model_used else ''}</i>"
            for chunk in _message_chunks(ai_response):
                await send(chat_id, f"{_html(chunk)}{footer}")
                footer = ""
    except Exception as exc:
        log.error("Chat-Fehler: %s", exc)
        await send(chat_id, f"❌ Fehler: {_html(exc)}", back_keyboard())


# --- DB ---------------------------------------------------------------------

async def get_db() -> Optional[asyncpg.Pool]:
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        except Exception as exc:
            log.warning("DB-Verbindung fehlgeschlagen: %s", exc)
            return None
    return db_pool


async def db_task_counts() -> dict:
    pool = await get_db()
    if pool is None:
        return {}
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """SELECT
                    COUNT(*) FILTER (WHERE status='pending')     AS pending,
                    COUNT(*) FILTER (WHERE status='in_progress') AS running,
                    COUNT(*) FILTER (WHERE status='completed')   AS completed,
                    COUNT(*) FILTER (WHERE status='failed')      AS failed
                FROM supervisor_tasks"""
            )
            return dict(row) if row else {}
        except Exception as exc:
            if not _supervisor_unavailable(exc):
                log.warning("Supervisor task count failed: %s", exc)
            return {}


async def db_tasks(limit: int = 10, status_filter: Optional[str] = None) -> list[dict]:
    pool = await get_db()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        try:
            if status_filter:
                rows = await conn.fetch(
                    "SELECT id, name, status, priority, assigned_agent, created_at "
                    "FROM supervisor_tasks WHERE status=$1 ORDER BY created_at DESC LIMIT $2",
                    status_filter,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT id, name, status, priority, assigned_agent, created_at "
                    "FROM supervisor_tasks ORDER BY created_at DESC LIMIT $1",
                    limit,
                )
            return [dict(row) for row in rows]
        except Exception as exc:
            if not _supervisor_unavailable(exc):
                log.warning("Supervisor task query failed: %s", exc)
            return []


async def db_task_by_id(task_id: str) -> Optional[dict]:
    pool = await get_db()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "SELECT id, name, description, status, priority, assigned_agent, created_at, updated_at "
                "FROM supervisor_tasks WHERE id=$1",
                task_id,
            )
            return dict(row) if row else None
        except Exception as exc:
            if not _supervisor_unavailable(exc):
                log.warning("Supervisor task detail query failed: %s", exc)
            return None


async def db_add_task(name: str, description: str, priority: str = "medium") -> str:
    pool = await get_db()
    if pool is None:
        raise RuntimeError("Postgres ist nicht erreichbar")
    task_id = f"telegram_{int(datetime.now().timestamp() * 1000)}"
    now = datetime.now()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO supervisor_tasks
                (id, name, description, priority, status, created_at, updated_at, metadata)
            VALUES ($1, $2, $3, $4, 'pending', $5, $6, $7::jsonb)
            RETURNING id
            """,
            task_id,
            name,
            description,
            priority,
            now,
            now,
            json.dumps({"source": "telegram"}),
        )
        return str(row["id"])


async def db_events(limit: int = 8) -> list[dict]:
    pool = await get_db()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                "SELECT timestamp, event_type, severity, message FROM supervisor_events "
                "ORDER BY timestamp DESC LIMIT $1",
                limit,
            )
            return [dict(row) for row in rows]
        except Exception as exc:
            if not _supervisor_unavailable(exc):
                log.warning("Supervisor events query failed: %s", exc)
            return []


# --- Keyboards / Screens ----------------------------------------------------

def main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Status", "callback_data": "menu:status"},
                {"text": "📋 Tasks", "callback_data": "menu:tasks"},
            ],
            [
                {"text": "➕ Task anlegen", "callback_data": "menu:add_task"},
                {"text": "📡 Events", "callback_data": "menu:events"},
            ],
            [{"text": "💬 Chat mit Agent", "callback_data": "menu:chat"}],
            [{"text": "🤖 Agent waehlen", "callback_data": "menu:agents"}],
            [{"text": "🔧 System", "callback_data": "menu:system"}],
        ]
    }


def agents_keyboard() -> dict:
    rows = []
    row: list[dict] = []
    for idx, agent in enumerate(AGENT_CATALOG):
        row.append({"text": agent["label"], "callback_data": f"agent:set:{agent['id']}"})
        if (idx + 1) % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "🏠 Hauptmenue", "callback_data": "menu:home"}])
    return {"inline_keyboard": rows}


def tasks_keyboard(tasks: list[dict]) -> dict:
    rows = []
    for task in tasks[:8]:
        icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(task.get("status", ""), "•")
        rows.append([{"text": f"{icon} {task['name'][:30]}", "callback_data": f"task:view:{task['id']}"}])
    rows.append([
        {"text": "➕ Neu", "callback_data": "menu:add_task"},
        {"text": "🏠 Menue", "callback_data": "menu:home"},
    ])
    return {"inline_keyboard": rows}


def back_keyboard(target: str = "menu:home") -> dict:
    return {"inline_keyboard": [[{"text": "🏠 Hauptmenue", "callback_data": target}]]}


def cancel_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "❌ Abbrechen", "callback_data": "menu:home"}]]}


def system_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🩺 Telegram Status", "callback_data": "sys:telegram"}],
            [{"text": "🔐 API Login", "callback_data": "sys:api"}],
            [{"text": "🏠 Hauptmenue", "callback_data": "menu:home"}],
        ]
    }


async def screen_home(user_name: str) -> tuple[str, dict]:
    counts = await db_task_counts()
    text = (
        f"👋 <b>Hey {_html(user_name)}!</b>\n\n"
        "<b>Kirobi OS</b> — Telegram-Bruecke ist aktiv.\n\n"
        "📊 <b>System-Uebersicht:</b>\n"
        f"  ⏳ Offene Tasks: <b>{counts.get('pending', '?')}</b>\n"
        f"  🔄 Aktive Tasks: <b>{counts.get('running', '?')}</b>\n\n"
        "Schreib einfach eine Nachricht oder waehle eine Aktion."
    )
    return text, main_menu_keyboard()


async def screen_status() -> tuple[str, dict]:
    counts = await db_task_counts()
    config = _config_state()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    text = (
        "📊 <b>System-Status</b>\n"
        f"🕐 {now}\n\n"
        "<b>Supervisor-Tasks:</b>\n"
        f"  ⏳ Pending: <b>{counts.get('pending', '?')}</b>\n"
        f"  🔄 In Arbeit: <b>{counts.get('running', '?')}</b>\n"
        f"  ✅ Completed: <b>{counts.get('completed', '?')}</b>\n"
        f"  ❌ Failed: <b>{counts.get('failed', '?')}</b>\n\n"
        "<b>Telegram:</b>\n"
        f"  Modus: <code>{_html(config['mode'])}</code>\n"
        f"  Auth: <code>{'bereit' if config['api_token_configured'] or config['api_login_configured'] else 'fehlt'}</code>"
    )
    return text, back_keyboard()


async def screen_tasks() -> tuple[str, dict]:
    tasks = await db_tasks(limit=10)
    if not tasks:
        return "📋 <b>Keine Tasks vorhanden.</b>\n\nLege einen neuen Task an.", back_keyboard()
    lines = [f"📋 <b>Aktuelle Tasks</b> ({len(tasks)} angezeigt)\n"]
    for task in tasks:
        icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(task.get("status", ""), "•")
        lines.append(f"{icon} <b>{_html(task['name'][:40])}</b> — Prio {_html(task['priority'])}")
    return "\n".join(lines), tasks_keyboard(tasks)


async def screen_task_detail(task_id: str) -> tuple[str, dict]:
    task = await db_task_by_id(task_id)
    if not task:
        return "❌ Task nicht gefunden.", back_keyboard("menu:tasks")
    icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(task.get("status", ""), "•")
    created = task["created_at"].strftime("%d.%m %H:%M") if task.get("created_at") else "?"
    text = (
        f"{icon} <b>{_html(task['name'])}</b>\n\n"
        f"📝 {_html(task.get('description') or 'Keine Beschreibung')}\n\n"
        f"Status: <b>{_html(task['status'])}</b>\n"
        f"Prioritaet: <b>{_html(task['priority'])}</b>\n"
        f"Agent: <b>{_html(task.get('assigned_agent') or 'nicht zugewiesen')}</b>\n"
        f"Erstellt: {created}"
    )
    return text, back_keyboard("menu:tasks")


async def screen_events() -> tuple[str, dict]:
    events = await db_events(limit=8)
    if not events:
        return "📡 <b>Keine Events vorhanden.</b>", back_keyboard()
    lines = ["📡 <b>Letzte Supervisor-Events</b>\n"]
    for event in events:
        timestamp = event["timestamp"].strftime("%d.%m %H:%M") if event.get("timestamp") else "?"
        severity = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}.get(event.get("severity", ""), "•")
        lines.append(f"{severity} <code>{timestamp}</code> {_html(str(event.get('message', ''))[:80])}")
    return "\n".join(lines), back_keyboard()


# --- Auth guard / handlers --------------------------------------------------

def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        log.warning("TELEGRAM_ALLOWED_USER_IDS leer — alle Anfragen abgelehnt")
        return False
    return user_id in ALLOWED_USER_IDS


async def handle_callback(callback_query: dict) -> None:
    callback_query_id = callback_query["id"]
    message = callback_query.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    user = callback_query.get("from", {})
    user_id = user.get("id", 0)
    user_name = user.get("first_name", "Unbekannt")
    data = callback_query.get("data", "")

    await answer_callback(callback_query_id)
    if not chat_id or not message_id:
        return
    if not is_authorized(user_id):
        await tg("answerCallbackQuery", callback_query_id=callback_query_id, text="Kein Zugriff", show_alert=True)
        return

    if data == "menu:home":
        text, keyboard = await screen_home(user_name)
    elif data == "menu:status":
        text, keyboard = await screen_status()
    elif data == "menu:tasks":
        text, keyboard = await screen_tasks()
    elif data == "menu:events":
        text, keyboard = await screen_events()
    elif data == "menu:system":
        text, keyboard = "🔧 <b>System</b>\n\nWaehle einen lokalen, sicheren Check.", system_keyboard()
    elif data == "menu:add_task":
        user_state[user_id] = {"state": "awaiting_task_name"}
        text, keyboard = "➕ <b>Neuer Task</b>\n\nWie soll der Task heissen?", cancel_keyboard()
    elif data == "menu:chat":
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
        user_state[user_id] = {"state": "chatting"}
        text, keyboard = (
            f"💬 <b>Chat-Modus aktiv.</b>\nAktiver Agent: {label}\nSchreib einfach los. /new startet frisch, /agents wechselt.",
            cancel_keyboard(),
        )
    elif data == "menu:agents":
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
        text, keyboard = (
            f"🤖 <b>Agent waehlen</b>\n\nAktiv: {label}\n\nJeder Agent hat eine eigene Konversation und sein eigenes Modell.",
            agents_keyboard(),
        )
    elif data.startswith("agent:set:"):
        agent_id = data.split(":", 2)[2]
        if agent_id not in AGENT_LOOKUP:
            text, keyboard = "❌ Unbekannter Agent.", agents_keyboard()
        else:
            active_agent_by_user[user_id] = agent_id
            user_state[user_id] = {"state": "chatting"}
            agent_meta = AGENT_LOOKUP[agent_id]
            text, keyboard = (
                f"✅ Aktiver Agent: <b>{agent_meta['label']}</b>\n<i>{agent_meta['desc']}</i>\n\n"
                f"Schreib mir jetzt direkt — ich antworte als {agent_meta['label']}.\n"
                f"/new = frische Konversation, /agents = wechseln.",
                cancel_keyboard(),
            )
    elif data.startswith("task:view:"):
        text, keyboard = await screen_task_detail(data.split(":")[-1])
    elif data == "sys:telegram":
        config = _config_state()
        text = (
            "🩺 <b>Telegram-Bridge</b>\n\n"
            f"Bot-Token: <code>{'gesetzt' if config['bot_token_configured'] else 'fehlt'}</code>\n"
            f"Allowed Users: <code>{'gesetzt' if config['allowed_users_configured'] else 'fehlt'}</code>\n"
            f"Modus: <code>{_html(config['mode'])}</code>"
        )
        keyboard = back_keyboard("menu:system")
    elif data == "sys:api":
        token = await get_api_token(force_refresh=True)
        text = f"🔐 <b>API Login:</b> <code>{'bereit' if token else 'nicht bereit'}</code>"
        keyboard = back_keyboard("menu:system")
    else:
        text, keyboard = await screen_home(user_name)

    await edit_msg(chat_id, message_id, text, keyboard)


async def handle_message(chat_id: int, user_id: int, text: str, user_name: str) -> None:
    if not is_authorized(user_id):
        await send(chat_id, "⛔ Zugriff verweigert.")
        return

    stripped = text.strip()
    state = user_state.get(user_id, {}).get("state", "idle")

    if stripped in ("/start", "/help"):
        user_state[user_id] = {"state": "idle"}
        screen_text, keyboard = await screen_home(user_name)
        await send(chat_id, screen_text, keyboard)
        return

    if stripped.startswith("/"):
        parts = stripped.split(None, 1)
        command = parts[0].lstrip("/").split("@")[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""
        await handle_slash(chat_id, user_id, user_name, command, args)
        return

    if state == "awaiting_task_name":
        user_state[user_id] = {"state": "awaiting_task_desc", "task_name": stripped}
        await send(chat_id, f"✏️ <b>Task:</b> {_html(stripped)}\n\nGib jetzt eine kurze Beschreibung ein.", cancel_keyboard())
        return

    if state == "awaiting_task_desc":
        task_name = user_state.get(user_id, {}).get("task_name", "Telegram Task")
        user_state[user_id] = {"state": "idle"}
        try:
            task_id = await db_add_task(task_name, stripped)
            await send(chat_id, f"✅ <b>Task erstellt!</b>\n\n📌 <b>{_html(task_name)}</b>\n🆔 <code>{_html(task_id)}</code>", back_keyboard())
        except Exception as exc:
            await send(chat_id, f"❌ Fehler beim Erstellen: {_html(exc)}", back_keyboard())
        return

    user_state[user_id] = {"state": "chatting"}
    await send_to_kirobi(chat_id, user_id, stripped)


async def handle_slash(chat_id: int, user_id: int, user_name: str, command: str, args: str) -> None:
    if command == "status":
        text, keyboard = await screen_status()
        await send(chat_id, text, keyboard)
    elif command == "tasks":
        text, keyboard = await screen_tasks()
        await send(chat_id, text, keyboard)
    elif command == "events":
        text, keyboard = await screen_events()
        await send(chat_id, text, keyboard)
    elif command == "chat":
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
        user_state[user_id] = {"state": "chatting"}
        await send(chat_id, f"💬 <b>Chat-Modus aktiv.</b>\nAktiver Agent: {label}\nSchreib einfach los.", cancel_keyboard())
    elif command in {"new", "reset"}:
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        conversation_by_user.pop((user_id, agent), None)
        label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
        user_state[user_id] = {"state": "chatting"}
        await send(chat_id, f"✅ <b>Neue Konversation mit {label} gestartet.</b>\nSchreib einfach los.", cancel_keyboard())
    elif command == "agents":
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
        await send(
            chat_id,
            f"🤖 <b>Agent waehlen</b>\n\nAktiv: {label}\n\nJeder Agent = eigenes Profil, eigenes Modell, eigene Konversation.",
            agents_keyboard(),
        )
    elif command == "agent":
        target = args.strip().lower().lstrip("@")
        if not target:
            agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
            label = AGENT_LOOKUP.get(agent, {}).get("label", agent)
            await send(chat_id, f"🤖 Aktiver Agent: <b>{label}</b>\n\nNutze /agents zum Wechseln oder <code>/agent &lt;id&gt;</code>.", agents_keyboard())
        elif target in AGENT_LOOKUP:
            active_agent_by_user[user_id] = target
            user_state[user_id] = {"state": "chatting"}
            meta = AGENT_LOOKUP[target]
            await send(chat_id, f"✅ Aktiver Agent: <b>{meta['label']}</b>\n<i>{meta['desc']}</i>\n\nSchreib einfach los.", cancel_keyboard())
        else:
            await send(chat_id, f"❌ Unbekannter Agent <code>{_html(target)}</code>.\n\nVerfuegbar:\n" + "\n".join(f"• <code>{a['id']}</code> — {a['label']}" for a in AGENT_CATALOG), agents_keyboard())
    elif command == "who":
        agent = active_agent_by_user.get(user_id, DEFAULT_AGENT)
        meta = AGENT_LOOKUP.get(agent, {"label": agent, "desc": ""})
        await send(chat_id, f"🤖 Aktiver Agent: <b>{meta['label']}</b>\n<i>{meta.get('desc','')}</i>\n\n/agents zum Wechseln.")
    elif command == "add":
        if args:
            parts = args.split("|", 1)
            task_name = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else task_name
            try:
                task_id = await db_add_task(task_name, description)
                await send(chat_id, f"✅ Task <b>{_html(task_name)}</b> erstellt.\nID: <code>{_html(task_id)}</code>", back_keyboard())
            except Exception as exc:
                await send(chat_id, f"❌ Fehler beim Erstellen: {_html(exc)}", back_keyboard())
        else:
            user_state[user_id] = {"state": "awaiting_task_name"}
            await send(chat_id, "➕ <b>Neuer Task</b>\n\nWie soll der Task heissen?", cancel_keyboard())
    else:
        screen_text, keyboard = await screen_home(user_name)
        await send(chat_id, screen_text, keyboard)


async def process_update(update: dict) -> None:
    if "callback_query" in update:
        await handle_callback(update["callback_query"])
        return

    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    user_id = user.get("id", 0)
    user_name = user.get("first_name") or user.get("username") or "Unbekannt"
    text = message.get("text", "").strip()
    if text:
        await handle_message(chat_id, user_id, text, user_name)


# --- Polling / FastAPI ------------------------------------------------------

async def polling_loop() -> None:
    log.info("Long-Polling gestartet")
    offset = 0
    while True:
        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(
                    f"{TELEGRAM_API}/getUpdates",
                    json={"offset": offset, "timeout": 30, "limit": 100},
                )
            data = _response_json(response)
            updates = data.get("result", []) if data.get("ok") else []
            for update in updates:
                offset = update["update_id"] + 1
                asyncio.create_task(process_update(update))
        except asyncio.CancelledError:
            break
        except Exception as exc:
            log.error("Polling-Fehler: %s", exc)
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN fehlt — Bot inaktiv")
    else:
        log.info("KeyCodi Telegram-Bot v2 startet. Autorisierte User-Anzahl: %s", len(ALLOWED_USER_IDS))
        await set_bot_commands()
        await get_api_token()

        if WEBHOOK_HOST:
            webhook_url = f"{WEBHOOK_HOST.rstrip('/')}{WEBHOOK_PATH}"
            result = await tg("setWebhook", url=webhook_url, drop_pending_updates=True)
            log.info("Webhook gesetzt: %s", result.get("ok"))
        else:
            asyncio.create_task(polling_loop())

        if NOTIFY_CHANNEL_ID and NOTIFY_ON_START:
            try:
                await send(
                    NOTIFY_CHANNEL_ID,
                    "🚀 <b>KeyCodi Telegram-Bot gestartet</b>\n"
                    f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Sende /start um das Menue zu oeffnen.",
                    log_failures=False,
                )
            except Exception as exc:
                log.warning("Startup-Notify fehlgeschlagen: %s", exc)

    yield

    # Shutdown
    global db_pool, api_token_cache
    if db_pool:
        await db_pool.close()
    db_pool = None
    api_token_cache = None
    if BOT_TOKEN and WEBHOOK_HOST:
        await tg("deleteWebhook", drop_pending_updates=True)


app = FastAPI(title="Kirobi Telegram Bot", version="2.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "telegram-bot", "version": "2.0"}


@app.get("/ready")
async def ready():
    config = _config_state()
    is_ready = bool(
        config["bot_token_configured"]
        and config["allowed_users_configured"]
        and (config["api_token_configured"] or config["api_login_configured"])
    )
    return {
        "status": "ready" if is_ready else "degraded",
        "service": "telegram-bot",
        "version": "2.0",
        "config": config,
        "active_conversations": len(conversation_by_user),
    }


@app.get("/telegram/status")
async def telegram_status():
    result = {"status": "unknown", "service": "telegram-bot", "config": _config_state()}
    if not BOT_TOKEN:
        result["status"] = "degraded"
        result["telegram"] = {"ok": False, "error": "bot token not configured"}
        return result

    data = await tg("getMe")
    bot = data.get("result", {}) if data.get("ok") else {}
    result["status"] = "ready" if data.get("ok") else "degraded"
    result["telegram"] = {
        "ok": bool(data.get("ok")),
        "id": bot.get("id"),
        "username": bot.get("username"),
        "first_name": bot.get("first_name"),
    }
    return result


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    try:
        update = await request.json()
        asyncio.create_task(process_update(update))
    except Exception as exc:
        log.error("Webhook-Fehler: %s", exc)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
