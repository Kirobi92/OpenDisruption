"""
services/telegram/keycodi/cron.py
Intelligente Cron-Jobs: Nur wirklich relevante Updates an Sven senden.

Jobs:
  1. status_report    — Alle 30 Min: Echter System-Status mit Kontext (nur wenn etwas notable)
  2. failure_check    — Alle 30 Min: Fehler-Tasks → automatische Retry-Planung
  3. decision_remind  — Alle 15 Min: Offene Entscheidungen an Sven erinnern
  4. alert_monitor    — Alle 5 Min: Sofort-Alerts bei kritischen Problemen
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from datetime import datetime
from html import escape
from pathlib import Path

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

# Tracking für Noise-Reduction: nur senden wenn sich etwas geändert hat
_last_state: dict = {}


# ─── System-Ressourcen ────────────────────────────────────────────────────────

def _ram_status() -> tuple[str, float]:
    """Gibt RAM-Status-String und Auslastungs-% zurück."""
    try:
        meminfo = Path("/proc/meminfo").read_text()
        data = {}
        for line in meminfo.splitlines():
            key, val = line.split(":", 1)
            data[key.strip()] = int(val.strip().split()[0])
        total_gb = data["MemTotal"] / 1024 / 1024
        avail_gb = data["MemAvailable"] / 1024 / 1024
        used_gb = total_gb - avail_gb
        pct = used_gb / total_gb * 100
        return f"🧮 RAM: {used_gb:.1f}/{total_gb:.1f}GB ({pct:.0f}%)", pct
    except Exception:
        return "🧮 RAM: nicht lesbar", 0.0


def _cpu_status() -> tuple[str, float]:
    """Gibt CPU-Last-String und Load-% zurück."""
    try:
        loadavg = Path("/proc/loadavg").read_text().split()
        load1 = float(loadavg[0])
        cpu_count = len(Path("/proc/cpuinfo").read_text().split("processor\t:")) - 1
        pct = min(load1 / max(cpu_count, 1) * 100, 100)
        return f"⚙️ CPU: Load {load1:.2f} ({pct:.0f}%)", pct
    except Exception:
        return "⚙️ CPU: nicht lesbar", 0.0


def _disk_status() -> tuple[str, float]:
    """Gibt Disk-Status und freien Platz in % zurück."""
    try:
        import shutil
        usage = shutil.disk_usage("/")
        free_gb = usage.free / 1024**3
        total_gb = usage.total / 1024**3
        pct_used = (usage.used / usage.total) * 100
        warn = " ⚠️" if pct_used > 85 else ""
        return f"💾 Disk: {free_gb:.1f}GB frei / {total_gb:.0f}GB{warn}", 100 - pct_used
    except Exception:
        return "💾 Disk: nicht lesbar", 100.0


def _gpu_status() -> tuple[str, dict]:
    """Gibt GPU-Status-String und Metriken-Dict zurück."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
             "--format=csv,noheader,nounits"],
            timeout=5,
        ).decode().strip()
        name, gpu_util, mem_used, mem_total, temp, power = [x.strip() for x in out.split(",")]
        gpu_int = int(gpu_util)
        mem_used_int = int(mem_used)
        mem_total_int = int(mem_total)
        temp_int = int(temp)
        power_f = float(power)
        metrics = {
            "gpu_util": gpu_int,
            "mem_used_mb": mem_used_int,
            "mem_total_mb": mem_total_int,
            "temp": temp_int,
            "power": power_f,
        }
        hot = " 🔥" if temp_int > 80 else ""
        busy = " 🚀" if gpu_int > 50 else ""
        return (
            f"🎮 GPU: {name} | {gpu_int}%{busy} | "
            f"VRAM {mem_used_int//1024}GB/{mem_total_int//1024}GB | "
            f"{temp_int}°C{hot} | {power_f:.0f}W"
        ), metrics
    except Exception:
        return "🎮 GPU: keine NVIDIA-GPU / nicht erreichbar", {}


async def _docker_status() -> tuple[str, list[str]]:
    """Gibt Docker-Container-Status zurück. Liefert Liste der DOWN-Container."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "--project-directory", "/home/sven/OpenDisruption",
            "ps", "--format", "{{.Name}}:{{.Status}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=8)
        lines = stdout.decode().strip().splitlines()
        down = []
        running_count = 0
        for line in lines:
            if ":" in line:
                name, status = line.split(":", 1)
                if "Up" in status or "running" in status.lower():
                    running_count += 1
                else:
                    down.append(name.replace("kirobi-", ""))
        total = len(lines)
        status_str = f"🐳 Docker: {running_count}/{total} Container laufen"
        if down:
            status_str += f" | ❌ Down: {', '.join(down[:5])}"
        return status_str, down
    except Exception as exc:
        log.debug("docker_status: %s", exc)
        return "🐳 Docker: Status nicht lesbar", []


async def _service_health_check() -> tuple[str, list[str]]:
    """Schneller Health-Check der wichtigsten Backend-Services."""
    services = [
        ("api", "http://127.0.0.1:8003/health"),
        ("auth", "http://127.0.0.1:8002/health"),
        ("ollama", "http://127.0.0.1:11434/"),
        ("embeddings", "http://127.0.0.1:8004/health"),
        ("retrieval", "http://127.0.0.1:8006/health"),
        ("analytics", "http://127.0.0.1:8010/health"),
    ]
    down: list[str] = []
    up: list[str] = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in services:
            try:
                r = await client.get(url)
                if r.status_code < 500:
                    up.append(name)
                else:
                    down.append(name)
            except Exception:
                down.append(name)
    status_str = f"🔌 Services: {len(up)}/{len(services)} erreichbar"
    if down:
        status_str += f" | ❌ {', '.join(down)}"
    return status_str, down


def _is_notable(counts: dict, down_services: list, down_containers: list,
                gpu_metrics: dict, ram_pct: float, cpu_pct: float) -> tuple[bool, list[str]]:
    """Prüft ob der Report wirklich etwas Interessantes enthält."""
    reasons: list[str] = []
    global _last_state

    # Tasks mit Fehlern
    failed = counts.get("failed", 0)
    if failed and failed > 0:
        reasons.append(f"{failed} Task(s) fehlgeschlagen")

    # Sofort-Tasks
    sofort = counts.get("sofort", 0)
    if sofort and sofort > 0:
        reasons.append(f"{sofort} SOFORT-Task(s) offen")

    # Services down
    if down_services:
        reasons.append(f"Services offline: {', '.join(down_services)}")
    if down_containers:
        reasons.append(f"Container down: {', '.join(down_containers)}")

    # Ressourcen-Warnungen
    if ram_pct > 85:
        reasons.append(f"RAM-Auslastung hoch: {ram_pct:.0f}%")
    if cpu_pct > 80:
        reasons.append(f"CPU-Last hoch: {cpu_pct:.0f}%")
    if gpu_metrics.get("temp", 0) > 85:
        reasons.append(f"GPU-Temperatur hoch: {gpu_metrics['temp']}°C")

    # Disk-Warnungen (kritisch: <5GB frei oder >92% belegt)
    try:
        import shutil as _shutil
        _du = _shutil.disk_usage("/")
        _free_gb = _du.free / 1024**3
        _pct_used = _du.used / _du.total * 100
        if _free_gb < 5.0:
            reasons.append(f"🚨 Disk KRITIS: nur {_free_gb:.1f}GB frei!")
        elif _pct_used > 90:
            reasons.append(f"Disk voll: {_pct_used:.0f}% belegt ({_free_gb:.1f}GB frei)")
    except Exception:
        pass

    # Tasks-Delta: Hat sich etwas verändert seit letztem Report?
    last_counts = _last_state.get("counts", {})
    new_completed = counts.get("completed", 0) - last_counts.get("completed", 0)
    if new_completed > 0:
        reasons.append(f"{new_completed} neue Task(s) erledigt")

    new_running = counts.get("running", 0)
    if new_running > 0 and new_running != last_counts.get("running", 0):
        reasons.append(f"{new_running} Task(s) aktiv")

    # Update State
    _last_state["counts"] = counts

    # Immer senden wenn es Gründe gibt, sonst nur alle 6h (12 * 30min)
    report_count = _last_state.get("report_count", 0)
    _last_state["report_count"] = report_count + 1
    if report_count % 12 == 0:
        reasons.insert(0, "Regelmäßiger 6h-Report")

    return len(reasons) > 0, reasons


# ─── Report-Aufbau ────────────────────────────────────────────────────────────

async def _build_status_report() -> tuple[str, bool]:
    """
    Baut einen intelligenten Status-Report.
    Gibt (report_text, should_send) zurück.
    should_send=False wenn nichts Bemerkenswertes passiert ist.
    """
    # Alle Daten parallel sammeln
    counts_task = db.task_counts()
    events_task = db.events_recent(limit=5)
    decisions_task = db.decision_pending()
    llm_task = is_available()
    models_task = loaded_models()
    docker_task = _docker_status()
    health_task = _service_health_check()

    (counts, events, pending_decisions, llm_ok, models,
     (docker_str, down_containers),
     (health_str, down_services)) = await asyncio.gather(
        counts_task, events_task, decisions_task, llm_task, models_task,
        docker_task, health_task,
    )

    gpu_str, gpu_metrics = _gpu_status()
    ram_str, ram_pct = _ram_status()
    cpu_str, cpu_pct = _cpu_status()
    disk_str, _ = _disk_status()

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    notable, reasons = _is_notable(counts, down_services, down_containers,
                                    gpu_metrics, ram_pct, cpu_pct)

    if not notable:
        return "", False

    # Header mit Begründung
    if len(reasons) == 1 and reasons[0].startswith("Regelmäßiger"):
        header = f"📊 <b>Kirobi Status</b> — {now}"
        intro = "Alles normal. Hier ist dein 6h-Überblick:\n"
    else:
        header = f"🔔 <b>Kirobi Meldung</b> — {now}"
        intro = "Wichtige Ereignisse:\n" + "\n".join(f"  • {r}" for r in reasons if not r.startswith("Regel")) + "\n"

    model_names = ", ".join(m.get("name", "?") for m in models) if models else "—"

    lines = [
        header,
        "",
        intro,
        "🖥 <b>System:</b>",
        f"  {gpu_str}",
        f"  {ram_str}",
        f"  {cpu_str}",
        f"  {disk_str}",
        f"  🧠 Ollama: {'✅ bereit' if llm_ok else '❌ nicht erreichbar'}",
        f"  📦 Modelle: <code>{escape(model_names)}</code>",
        "",
        "🐳 <b>Infrastruktur:</b>",
        f"  {docker_str}",
        f"  {health_str}",
        "",
        "📋 <b>Tasks:</b>",
        f"  ⏳ Pending: <b>{counts.get('pending', '?')}</b>  "
        f"🔄 Aktiv: <b>{counts.get('running', '?')}</b>  "
        f"✅ Erledigt: <b>{counts.get('completed', '?')}</b>",
    ]

    failed_count = counts.get("failed", 0)
    if failed_count and failed_count > 0:
        lines.append(f"  ❌ <b>Fehler: {failed_count}</b> — werden automatisch retryed")

    sofort_count = counts.get("sofort", 0)
    if sofort_count and sofort_count > 0:
        lines.append(f"  🚨 <b>SOFORT: {sofort_count}</b> — sofortige Erledigung nötig!")

    # Git-Aktivität der letzten 6h
    try:
        import subprocess as _sp
        git_out = _sp.check_output(
            ["git", "-C", "/home/sven/OpenDisruption", "log",
             "--oneline", "--since=6 hours ago", "--max-count=5"],
            timeout=5, stderr=_sp.DEVNULL,
        ).decode().strip()
        if git_out:
            lines += ["", "📝 <b>Letzte Git-Commits:</b>"]
            for gl in git_out.splitlines()[:4]:
                lines.append(f"  • <code>{escape(gl[:72])}</code>")
    except Exception:
        pass

    # Wichtige Events (nur Warnings und Errors)
    important_events = [
        e for e in events
        if e.get("severity") in ("warning", "error", "critical")
    ]
    if important_events:
        lines += ["", "⚡ <b>Wichtige Events:</b>"]
        for e in important_events[:4]:
            sev = {"warning": "⚠️", "error": "❌", "critical": "🚨"}.get(e.get("severity", ""), "ℹ️")
            ts = e["timestamp"].strftime("%H:%M") if e.get("timestamp") else "?"
            msg = escape(str(e.get("message", ""))[:80])
            lines.append(f"  {sev} {ts}: {msg}")

    if pending_decisions:
        lines += [
            "",
            f"❓ <b>{len(pending_decisions)} Entscheidung(en) warten auf dich:</b>",
        ]
        for d in pending_decisions[:2]:
            lines.append(f"  • {escape(str(d.get('question',''))[:80])}")
        lines.append("  → /decisions")

    return "\n".join(lines), True


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


async def _send_alert(chat_ids: list, message: str) -> None:
    """Sofort-Alert an alle konfigurierten Chats senden."""
    for chat_id in chat_ids:
        try:
            await send(chat_id, message)
        except Exception as exc:
            log.warning("Alert senden an %s fehlgeschlagen: %s", chat_id, exc)


# ─── Cron-Loop ───────────────────────────────────────────────────────────────

async def _cron_loop(notify_chat_ids: list[str | int]) -> None:
    """Hauptloop — intelligente Reports + sofortige Alerts bei kritischen Ereignissen."""
    global _running
    interval = CRON_REPORT_INTERVAL_MIN * 60
    decision_interval = 15 * 60
    alert_interval = 5 * 60
    last_decision_remind = 0.0
    last_alert_check = 0.0
    _last_alert_state: dict = {}

    log.info("Cron-Loop gestartet (Intervall: %d Min)", CRON_REPORT_INTERVAL_MIN)

    while _running:
        await asyncio.sleep(30)
        if not _running:
            break

        now = time.monotonic()

        # ── Sofort-Alert-Check alle 5 Min ──────────────────────────────────
        if now - last_alert_check >= alert_interval:
            last_alert_check = now
            try:
                counts = await db.task_counts()
                sofort = counts.get("sofort", 0)
                failed = counts.get("failed", 0)

                # Neue SOFORT-Tasks?
                prev_sofort = _last_alert_state.get("sofort", 0)
                if sofort and sofort > prev_sofort:
                    await _send_alert(
                        notify_chat_ids,
                        f"🚨 <b>SOFORT-TASK HINZUGEKOMMEN!</b>\n\n"
                        f"Es gibt jetzt <b>{sofort}</b> offene SOFORT-Task(s).\n"
                        f"Bitte umgehend prüfen → /tasks",
                    )
                _last_alert_state["sofort"] = sofort or 0

                # Neue Fehler?
                prev_failed = _last_alert_state.get("failed", 0)
                if failed and failed > prev_failed:
                    diff = failed - prev_failed
                    await _send_alert(
                        notify_chat_ids,
                        f"❌ <b>{diff} neuer Fehler</b> in Tasks\n\n"
                        f"Gesamt fehlgeschlagen: {failed}\n"
                        f"KeyCodi plant automatischen Retry.\n→ /tasks für Details",
                    )
                _last_alert_state["failed"] = failed or 0

            except Exception as exc:
                log.debug("alert_check: %s", exc)

        # ── Entscheidungs-Reminder alle 15 Min ─────────────────────────────
        if now - last_decision_remind >= decision_interval:
            last_decision_remind = now
            try:
                pending = await db.decision_pending()
                if pending:
                    lines = [f"❓ <b>{len(pending)} Entscheidung(en) warten auf dich!</b>", ""]
                    for d in pending[:3]:
                        lines.append(f"• {escape(str(d.get('question', ''))[:100])}")
                    lines.append("\n→ /decisions")
                    for chat_id in notify_chat_ids:
                        try:
                            await send(chat_id, "\n".join(lines))
                        except Exception as exc:
                            log.warning("Decision-Reminder fehlgeschlagen: %s", exc)
            except Exception as exc:
                log.debug("decision_remind: %s", exc)

        # ── Haupt-Report alle CRON_REPORT_INTERVAL_MIN ─────────────────────
        elapsed = now - _last_state.get("last_report_time", 0.0)
        if elapsed >= interval:
            _last_state["last_report_time"] = now

            # Parallel: Report bauen + Failures prüfen
            (report, should_send), _ = await asyncio.gather(
                _build_status_report(),
                _check_and_retry_failures(),
            )

            if should_send and report:
                await db.cron_report_save(report, "status")
                for chat_id in notify_chat_ids:
                    try:
                        await send(chat_id, report)
                    except Exception as exc:
                        log.warning("Cron-Report senden an %s fehlgeschlagen: %s", chat_id, exc)
            else:
                log.debug("Cron-Report übersprungen — nichts Bemerkenswertes")


def start_cron(notify_chat_ids: list[str | int]) -> asyncio.Task:
    global _running
    _running = True
    return asyncio.create_task(_cron_loop(notify_chat_ids))


def stop_cron() -> None:
    global _running
    _running = False
