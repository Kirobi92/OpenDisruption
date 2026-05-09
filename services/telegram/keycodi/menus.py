"""
services/telegram/keycodi/menus.py
Alle Inline-Keyboards und Screen-Texte für den KeyCodi Telegram Bot.

Menü-Hierarchie:
  🏠 KeyCodi-Menü
  ├── 💬 KeyCodi       (direkter Chat)
  ├── 📊 Status        (System, GPU, LLM, Aufgaben)
  ├── 📋 Aufgaben      (Liste, Detail, Anlegen)
  ├── ❓ Entscheidungen (offene Fragen von Agenten)
  ├── 📡 Ereignisse    (letzte Ereignisse)
  ├── 📚 Vault         (MOC, Daily Note, Suche)
  ├── 🤖 Agenten       (KeyCodi + weitere Agentenoberflächen)
  ├── ⚙️ Hardware      (GPU/CPU/RAM Auslastung, Modelle)
  └── 🔧 System        (Bot/API/Konfiguration)
"""
from __future__ import annotations

from html import escape as _e
from datetime import datetime
from typing import Optional

from . import db
from .config import KIROBI_TELEGRAM_WEB_BASE_URL
from .llm import available_models, is_available, loaded_models, provider


# ─── Keyboards ───────────────────────────────────────────────────────────────


def _surface_url(path: str) -> str:
    base = KIROBI_TELEGRAM_WEB_BASE_URL or "http://kirobi.local"
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"

def kb_main() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "💬 KeyCodi",      "callback_data": "m:chat"},
                {"text": "🤝 Copilot",      "callback_data": "m:copilot"},
            ],
            [
                {"text": "📊 Status",       "callback_data": "m:status"},
                {"text": "📋 Aufgaben",     "callback_data": "m:tasks"},
            ],
            [
                {"text": "🌐 Oberflächen",  "callback_data": "m:surfaces"},
                {"text": "❓ Entscheidungen", "callback_data": "m:decisions"},
            ],
            [
                {"text": "📡 Ereignisse",   "callback_data": "m:events"},
                {"text": "📚 Vault",        "callback_data": "m:vault"},
            ],
            [
                {"text": "🤖 Agenten",      "callback_data": "m:agents"},
                {"text": "⚙️ Hardware",     "callback_data": "m:hardware"},
            ],
            [
                {"text": "🔧 System",       "callback_data": "m:system"},
                {"text": "♻️ Neuer Chat",    "callback_data": "m:reset_chat"},
            ],
        ]
    }


def kb_surfaces() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "💬 Chat", "url": _surface_url("/chat?zone=WORKSPACE")},
                {"text": "🔎 Suche", "url": _surface_url("/search?zone=WORKSPACE")},
            ],
            [
                {"text": "📤 Upload", "url": _surface_url("/upload?zone=WORKSPACE")},
                {"text": "⚙️ Settings", "url": _surface_url("/settings?section=permissions")},
            ],
            [
                {"text": "🛡 Dashboard", "url": _surface_url("/dashboard/?section=control")},
                {"text": "📋 Admin Tasks", "url": _surface_url("/dashboard/tasks?filter=blocked")},
            ],
            [
                {"text": "🧩 Services", "url": _surface_url("/dashboard/?section=services")},
                {"text": "🧪 Workbench", "callback_data": "m:workbench"},
            ],
            [{"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"}],
        ]
    }


def kb_workbench() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🧠 Open WebUI", "url": _surface_url("/open-webui/")},
                {"text": "🔀 Flowise", "url": _surface_url("/flowise/")},
            ],
            [
                {"text": "🗂 Qdrant", "url": _surface_url("/qdrant/dashboard")},
                {"text": "📊 Services", "url": _surface_url("/dashboard/services")},
            ],
            [
                {"text": "◀️ Oberflächen", "callback_data": "m:surfaces"},
                {"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"},
            ],
        ]
    }


def kb_back(target: str = "m:home") -> dict:
    return {"inline_keyboard": [[{"text": "🏠 KeyCodi-Menü", "callback_data": target}]]}


def kb_back_tasks() -> dict:
    return {"inline_keyboard": [
        [
            {"text": "◀️ Aufgaben", "callback_data": "m:tasks"},
            {"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"},
        ]
    ]}


def kb_cancel() -> dict:
    return {"inline_keyboard": [[{"text": "❌ Zurück zu KeyCodi", "callback_data": "m:home"}]]}


def kb_tasks(tasks: list[dict]) -> dict:
    rows = []
    for t in tasks[:10]:
        icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(
            t.get("status", ""), "•"
        )
        sofort = " 🚨" if t.get("sofort") else ""
        rows.append([{
            "text": f"{icon}{sofort} {t['name'][:28]}",
            "callback_data": f"task:v:{t['id'][:20]}",
        }])
    rows.append([
        {"text": "➕ Neuer Task",        "callback_data": "m:add_task"},
        {"text": "🚨 SOFORT-Task",       "callback_data": "m:add_sofort"},
        {"text": "🏠 KeyCodi-Menü",      "callback_data": "m:home"},
    ])
    return {"inline_keyboard": rows}


def kb_agents() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🧑‍💻 OpenCode",   "callback_data": "agent:opencode"},
                {"text": "🌐 OpenClaw",    "callback_data": "agent:openclaw"},
            ],
            [
                {"text": "🧠 Hermes",      "callback_data": "agent:hermes"},
                {"text": "📖 Obsidian",    "callback_data": "agent:obsidian"},
            ],
            [
                {"text": "🔮 KIDI",        "callback_data": "agent:kidi"},
                {"text": "👑 KeyBrodi",    "callback_data": "agent:keybrodi"},
            ],
            [{"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"}],
        ]
    }


def kb_vault() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "📅 Daily Note anlegen",  "callback_data": "vault:daily"},
                {"text": "🗺 MOC generieren",      "callback_data": "vault:moc"},
            ],
            [
                {"text": "📄 Note lesen",           "callback_data": "vault:read_prompt"},
            ],
            [{"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"}],
        ]
    }


def kb_decisions(decisions: list[dict]) -> dict:
    rows = []
    for d in decisions[:5]:
        rows.append([{
            "text": f"❓ {d['question'][:35]}",
            "callback_data": f"dec:v:{d['id'][:20]}",
        }])
    rows.append([{"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"}])
    return {"inline_keyboard": rows}


def kb_decision_answer(decision_id: str, options: list[str]) -> dict:
    rows = []
    for i, opt in enumerate(options[:6]):
        rows.append([{
            "text": opt[:40],
            "callback_data": f"dec:ans:{decision_id[:20]}:{i}",
        }])
    rows.append([{"text": "✍️ Freitext-Antwort", "callback_data": f"dec:free:{decision_id[:20]}"}])
    rows.append([{"text": "🏠 KeyCodi-Menü", "callback_data": "m:home"}])
    return {"inline_keyboard": rows}


def kb_system() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🔐 API-Status",       "callback_data": "sys:api"}],
            [{"text": "🤖 Bot-Info",         "callback_data": "sys:bot"}],
            [{"text": "📋 Konfiguration",    "callback_data": "sys:config"}],
            [{"text": "🏠 KeyCodi-Menü",     "callback_data": "m:home"}],
        ]
    }


# ─── Screen-Builder ──────────────────────────────────────────────────────────

async def screen_home(user_name: str) -> tuple[str, dict]:
    counts = await db.task_counts()
    now = datetime.now().strftime("%H:%M")
    text = (
        f"👋 <b>Hey {_e(user_name)}!</b> — {now}\n\n"
        "<b>KeyCodi</b> — dein direkter Code-Orchestrator für unterwegs\n\n"
        "📋 <b>Schnellübersicht:</b>\n"
        f"  ⏳ Pending: <b>{counts.get('pending', '?')}</b>  "
        f"🔄 Aktiv: <b>{counts.get('running', '?')}</b>  "
        f"❌ Fehler: <b>{counts.get('failed', '?')}</b>\n"
        + (f"  🚨 <b>SOFORT: {counts['sofort']}</b>\n" if counts.get('sofort') else "")
        + "\n\nWähle direkt, was du brauchst:"
    )
    return text, kb_main()


async def screen_status() -> tuple[str, dict]:
    import subprocess
    counts = await db.task_counts()
    llm_ok = await is_available()
    models = await loaded_models()
    llm_provider = provider()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # GPU
    try:
        raw = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            timeout=5,
        ).decode().strip()
        gpu_util, mem_used, mem_total, temp, power = [x.strip() for x in raw.split(",")]
        gpu_line = (
            f"🎮 RTX 3090: <b>{gpu_util}%</b> | "
            f"VRAM {int(mem_used)//1024}GB/{int(mem_total)//1024}GB | "
            f"🌡 {temp}°C | ⚡{float(power):.0f}W"
        )
    except Exception:
        gpu_line = "🎮 GPU: nicht abfragbar"

    model_str = ", ".join(m.get("name", "?")[:20] for m in models[:3]) if models else "keine"

    text = (
        f"📊 <b>System-Status</b> — {now}\n\n"
        f"{gpu_line}\n"
        f"🧠 LLM: {'✅ bereit' if llm_ok else '❌ offline'} | "
        f"Provider: <code>{_e(llm_provider)}</code> | "
        f"Geladen: <code>{_e(model_str)}</code>\n\n"
        "<b>Aufgaben:</b>\n"
        f"  ⏳ Pending: <b>{counts.get('pending', '?')}</b>\n"
        f"  🔄 Aktiv: <b>{counts.get('running', '?')}</b>\n"
        f"  ✅ Erledigt: <b>{counts.get('completed', '?')}</b>\n"
        f"  ❌ Fehler: <b>{counts.get('failed', '?')}</b>\n"
        + (f"  🚨 <b>SOFORT: {counts.get('sofort', 0)}</b>\n" if counts.get('sofort') else "")
    )
    return text, kb_back()


async def screen_surfaces() -> tuple[str, dict]:
    text = (
        "🌐 <b>OpenDisruption Oberflächen</b>\n\n"
        "Direkter Zugriff auf die MVP-Flächen über genau einen sicheren Edge.\n\n"
        f"Basis: <code>{_e(KIROBI_TELEGRAM_WEB_BASE_URL or 'http://kirobi.local')}</code>\n\n"
        "• Chat, Suche, Upload und Settings für den täglichen MVP-Fluss\n"
        "• Dashboard, Tasks und Services für Operator-Steuerung\n"
        "• Workbench nur über LAN/Tailscale"
    )
    return text, kb_surfaces()


async def screen_workbench() -> tuple[str, dict]:
    text = (
        "🧪 <b>Workbench</b>\n\n"
        "Diese Flächen bleiben hinter Caddy und sind nur über LAN/Tailscale gedacht:\n"
        "Open WebUI, Flowise und Qdrant.\n\n"
        "Nutze sie für Admin-/Diagnose-Aufgaben, nicht als öffentliche Produktfläche."
    )
    return text, kb_workbench()


async def screen_tasks() -> tuple[str, dict]:
    tasks = await db.tasks_list(limit=12)
    if not tasks:
        return "📋 <b>Keine Aufgaben in der Queue.</b>\n\nLege bei Bedarf eine neue Aufgabe an.", kb_back()
    sofort_tasks = [t for t in tasks if t.get("sofort")]
    normal_tasks = [t for t in tasks if not t.get("sofort")]
    lines = [f"📋 <b>Aufgaben</b> ({len(tasks)} angezeigt)\n"]
    if sofort_tasks:
        lines.append("🚨 <b>SOFORT:</b>")
        for t in sofort_tasks:
            icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(t.get("status", ""), "•")
            lines.append(f"  {icon} {_e(t['name'][:40])}")
    if normal_tasks:
        lines.append("\n📋 <b>Queue:</b>")
        for t in normal_tasks[:8]:
            icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(t.get("status", ""), "•")
            lines.append(f"  {icon} {_e(t['name'][:40])}")
    return "\n".join(lines), kb_tasks(tasks)


async def screen_task_detail(task_id: str) -> tuple[str, dict]:
    task = await db.task_detail(task_id)
    if not task:
        return "❌ Task nicht gefunden.", kb_back("m:tasks")
    icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(task.get("status", ""), "•")
    sofort_badge = " 🚨 SOFORT" if task.get("sofort") else ""
    created = task["created_at"].strftime("%d.%m %H:%M") if task.get("created_at") else "?"
    text = (
        f"{icon} <b>{_e(task['name'])}</b>{sofort_badge}\n\n"
        f"📝 {_e(str(task.get('description') or 'Keine Beschreibung'))}\n\n"
        f"Status: <b>{_e(task['status'])}</b> | Prio: <b>{_e(task['priority'])}</b>\n"
        f"Agent: <b>{_e(task.get('assigned_agent') or '—')}</b>\n"
        f"Erstellt: {created}"
    )
    return text, kb_back_tasks()


async def screen_agents(agent_name: Optional[str] = None) -> tuple[str, dict]:
    agent_info = {
        "opencode":  ("🧑‍💻", "OpenCode",  "Coding-Oberfläche. Aktuell eher vorbereitend als voll autonom."),
        "openclaw":  ("🌐", "OpenClaw",  "Web-/API-orientierte Agentenoberfläche mit Fokus auf externe Recherchepfade."),
        "hermes":    ("🧠", "Hermes",    "Primärer Telegram-Agent für Analyse, Planung, Schlussfolgerungen und lokale Antworten."),
        "obsidian":  ("📖", "Obsidian",  "Vault-Notizen, Daily Notes, MOCs und strukturierte Wissenspflege."),
        "kidi":      ("🔮", "KIDI",      "Lokale Kontext- und Gedächtnisschicht für spätere Orchestrierung."),
        "keybrodi":  ("👑", "KeyBrodi",  "Geplante Orchestrierungsinstanz. Noch nicht der primäre Laufzeitpfad."),
    }
    if agent_name and agent_name in agent_info:
        icon, name, desc = agent_info[agent_name]
        text = f"{icon} <b>{name}</b>\n\n{_e(desc)}"
        return text, kb_back("m:agents")
    text = (
        "🤖 <b>Agenten-Übersicht</b>\n\n"
        "Hermes ist hier dein direkter Gesprächspartner. Die anderen Einträge zeigen den Status weiterer Agentenpfade."
    )
    return text, kb_agents()


async def screen_vault() -> tuple[str, dict]:
    text = (
        "📚 <b>Obsidian-Vault</b>\n\n"
        "Der Vault ist die Wissensbasis des Systems und wird über den Obsidian-Agenten bedient.\n\n"
        "Wähle eine Aktion:"
    )
    return text, kb_vault()


async def screen_hardware() -> tuple[str, dict]:
    import subprocess, os
    now = datetime.now().strftime("%H:%M")

    # GPU
    try:
        raw = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,clocks.current.sm",
             "--format=csv,noheader,nounits"],
            timeout=5,
        ).decode().strip()
        parts = [x.strip() for x in raw.split(",")]
        name, util, mem_used, mem_total, temp, power, clock = parts
        gpu_section = (
            f"🎮 <b>{_e(name)}</b>\n"
            f"  GPU-Util: <b>{util}%</b> | SM-Takt: {clock} MHz\n"
            f"  VRAM: <b>{int(mem_used)//1024}GB</b> / {int(mem_total)//1024}GB "
            f"({100*int(mem_used)//int(mem_total)}%)\n"
            f"  Temp: <b>{temp}°C</b> | Power: <b>{float(power):.0f}W</b> / 350W"
        )
    except Exception:
        gpu_section = "🎮 GPU: nicht abfragbar"

    # CPU
    try:
        load = os.getloadavg()
        cpu_section = (
            f"🖥 CPU: <b>{os.cpu_count()} Kerne</b> | "
            f"Load: {load[0]:.1f} / {load[1]:.1f} / {load[2]:.1f}"
        )
    except Exception:
        cpu_section = "🖥 CPU: nicht abfragbar"

    # RAM
    try:
        with open("/proc/meminfo") as f:
            info = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
        total = info.get("MemTotal", 0) // 1024
        free = info.get("MemAvailable", 0) // 1024
        used = total - free
        ram_section = f"💾 RAM: <b>{used}MB</b> / {total}MB ({100*used//total if total else 0}%)"
    except Exception:
        ram_section = "💾 RAM: nicht abfragbar"

    # LLM
    models = await loaded_models()
    model_str = "\n".join(
        f"  • {_e(m.get('name','?')[:30])} ({m.get('size_vram', '?')})"
        for m in models
    ) or "  keine Modelle geladen"

    text = (
        f"⚙️ <b>Hardware-Status</b> — {now}\n\n"
        f"{gpu_section}\n\n"
        f"{cpu_section}\n"
        f"{ram_section}\n\n"
        f"🧠 <b>Aktive Modelle (VRAM):</b>\n{model_str}\n\n"
        f"Parallele LLM-Requests: max. 4 (OLLAMA_NUM_PARALLEL)"
    )
    return text, kb_back()


async def screen_events() -> tuple[str, dict]:
    events = await db.events_recent(limit=10)
    if not events:
        return "📡 <b>Keine Events.</b>", kb_back()
    lines = ["📡 <b>Letzte Events</b>\n"]
    for e in events:
        sev_icon = {"warning": "⚠️", "error": "❌", "critical": "🚨"}.get(e.get("severity", ""), "ℹ️")
        ts = e["timestamp"].strftime("%d.%m %H:%M") if e.get("timestamp") else "?"
        lines.append(f"{sev_icon} <code>{ts}</code> {_e(str(e.get('message',''))[:70])}")
    return "\n".join(lines), kb_back()


async def screen_decisions() -> tuple[str, dict]:
    pending = await db.decision_pending()
    if not pending:
        return "✅ <b>Keine offenen Entscheidungen.</b>\n\nAlle Agenten laufen autonom.", kb_back()
    text = f"❓ <b>{len(pending)} offene Entscheidung(en)</b>\n\nWähle eine aus:"
    return text, kb_decisions(pending)


async def screen_decision_detail(decision_id: str) -> tuple[str, dict]:
    pool = await db.get_pool()
    if pool is None:
        return "❌ DB nicht erreichbar.", kb_back("m:decisions")
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, question, context, options FROM keycodi_decisions WHERE id=$1",
            decision_id,
        )
    if not row:
        return "❌ Entscheidung nicht gefunden.", kb_back("m:decisions")
    import json
    options = json.loads(row["options"]) if row["options"] else []
    text = (
        f"❓ <b>Entscheidung erforderlich</b>\n\n"
        f"<b>{_e(row['question'])}</b>\n\n"
        + (f"📝 {_e(row['context'])}\n\n" if row.get("context") else "")
        + ("Wähle eine Option:" if options else "Antworte mit freiem Text:")
    )
    return text, kb_decision_answer(decision_id, options)
