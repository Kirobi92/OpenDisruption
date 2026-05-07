"""
services/telegram/keycodi/cron.py
30-Minuten-Cron-Jobs: Status-Report an Sven + OpenCode-Benachrichtigung.

Jobs:
  1. status_report    — Alle 30 Min: Tasks, Events, LLM-Status, GPU-Auslastung
  2. failure_check    — Alle 30 Min: Fehler-Tasks → automatische Retry-Planung
  3. decision_remind  — Alle 15 Min: Offene Entscheidungen an Sven erinnern
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime
from html import escape

import httpx

from .config import (
    CRON_REPORT_INTERVAL_MIN,
    NOTIFY_CHANNEL_ID,
    OLLAMA_BASE_URL,
)
from . import db
from .tg import send
from .llm import is_available, loaded_models

log = logging.getLogger("keycodi.cron")

_running = False


# ─── GPU-Status (via nvidia-smi) ─────────────────────────────────────────────

def _gpu_status() -> str:
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            timeout=5,
        ).decode().strip()
        gpu_util, mem_used, mem_total, temp, power = [x.strip() for x in out.split(",")]
        return (
            f"🎮 GPU: {gpu_util}% | "
            f"VRAM: {int(mem_used)//1024}GB/{int(mem_total)//1024}GB | "
            f"🌡 {temp}°C | ⚡ {float(power):.0f}W"
        )
    except Exception:
        return "🎮 GPU: nicht abfragbar"


# ─── Einzelne Report-Sektionen ───────────────────────────────────────────────

async def _build_status_report() -> str:
    counts = await db.task_counts()
    events = await db.events_recent(limit=5)
    pending_decisions = await db.decision_pending()
    llm_ok = await is_available()
    models = await loaded_models()
    gpu = _gpu_status()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    model_names = ", ".join(m.get("name", "?") for m in models) if models else "keine"

    lines = [
        f"📊 <b>KeyCodi 30-Min-Report</b> — {now}",
        "",
        "🖥 <b>System:</b>",
        f"  {gpu}",
        f"  🧠 LLM: {'✅ bereit' if llm_ok else '❌ nicht erreichbar'}",
        f"  📦 Geladene Modelle: <code>{escape(model_names)}</code>",
        "",
        "📋 <b>Tasks:</b>",
        f"  ⏳ Pending: <b>{counts.get('pending', '?')}</b>",
        f"  🔄 Aktiv: <b>{counts.get('running', '?')}</b>",
        f"  ✅ Erledigt: <b>{counts.get('completed', '?')}</b>",
        f"  ❌ Fehler: <b>{counts.get('failed', '?')}</b>",
        f"  🚨 SOFORT: <b>{counts.get('sofort', 0)}</b>",
    ]

    if events:
        lines += ["", "📡 <b>Letzte Events:</b>"]
        for e in events[:3]:
            sev = {"warning": "⚠️", "error": "❌", "critical": "🚨"}.get(e.get("severity", ""), "ℹ️")
            ts = e["timestamp"].strftime("%H:%M") if e.get("timestamp") else "?"
            lines.append(f"  {sev} {ts} — {escape(str(e.get('message',''))[:60])}")

    if pending_decisions:
        lines += ["", f"❓ <b>Offene Entscheidungen: {len(pending_decisions)}</b>"]
        lines.append("  → /decisions aufrufen")

    failed_count = counts.get("failed", 0)
    if failed_count and failed_count > 0:
        lines += ["", f"⚠️ <b>{failed_count} fehlgeschlagene Tasks</b> — KeyCodi plant Retry"]

    return "\n".join(lines)


async def _check_and_retry_failures() -> None:
    """Fehlgeschlagene Tasks → Status zurücksetzen auf 'pending' für Retry."""
    pool = await db.get_pool()
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name FROM supervisor_tasks "
                "WHERE status='failed' AND metadata->>'retry_count' IS NULL "
                "ORDER BY created_at DESC LIMIT 5"
            )
            for row in rows:
                await conn.execute(
                    """UPDATE supervisor_tasks
                       SET status='pending',
                           updated_at=NOW(),
                           metadata = metadata || '{"retry_count": 1}'::jsonb
                       WHERE id=$1""",
                    row["id"],
                )
                log.info("Auto-Retry für Task: %s (%s)", row["name"], row["id"])
                await db.event_log(
                    "auto_retry",
                    f"KeyCodi: Auto-Retry für Task '{row['name']}'",
                    "info",
                    {"task_id": row["id"]},
                )
    except Exception as exc:
        log.warning("failure_check: %s", exc)


# ─── Cron-Loop ───────────────────────────────────────────────────────────────

async def _cron_loop(notify_chat_ids: list[str | int]) -> None:
    """Läuft als Hintergrund-Task — sendet alle CRON_REPORT_INTERVAL_MIN einen Report."""
    global _running
    interval = CRON_REPORT_INTERVAL_MIN * 60
    decision_interval = 15 * 60  # Entscheidungs-Reminder alle 15 Min
    last_decision_remind = 0.0

    import time
    log.info("Cron-Loop gestartet (Intervall: %d Min)", CRON_REPORT_INTERVAL_MIN)

    while _running:
        await asyncio.sleep(interval)
        if not _running:
            break

        # Parallel: Report bauen + Failures prüfen
        report, _ = await asyncio.gather(
            _build_status_report(),
            _check_and_retry_failures(),
        )

        # Report speichern
        await db.cron_report_save(report, "status")

        # Report senden
        for chat_id in notify_chat_ids:
            try:
                await send(chat_id, report)
            except Exception as exc:
                log.warning("Cron-Report senden an %s fehlgeschlagen: %s", chat_id, exc)

        # Entscheidungs-Reminder (alle 15 Min)
        now = time.monotonic()
        if now - last_decision_remind >= decision_interval:
            last_decision_remind = now
            pending = await db.decision_pending()
            if pending:
                reminder = (
                    f"❓ <b>{len(pending)} offene Entscheidung(en) warten auf dich!</b>\n\n"
                    + "\n".join(
                        f"• {escape(d['question'][:80])}"
                        for d in pending[:3]
                    )
                    + "\n\n→ /decisions aufrufen"
                )
                for chat_id in notify_chat_ids:
                    try:
                        await send(chat_id, reminder)
                    except Exception as exc:
                        log.warning("Decision-Reminder fehlgeschlagen: %s", exc)


def start_cron(notify_chat_ids: list[str | int]) -> asyncio.Task:
    global _running
    _running = True
    return asyncio.create_task(_cron_loop(notify_chat_ids))


def stop_cron() -> None:
    global _running
    _running = False
