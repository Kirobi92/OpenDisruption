#!/usr/bin/env python3
"""
Hermes Daily Briefing — sends a structured status report to Telegram.

Triggered via cron inside the hermes-runtime container (see crontab below):
  0 9,20 * * * /usr/bin/python3 /opt/jobs/daily_briefing.py >> /var/log/hermes/briefing.log 2>&1

Reads:
  - docker ps healthchecks
  - TECH_DEBT_REGISTER.md / IMPLEMENTATION_ROADMAP.md (next P0/P1 item)
  - core-events.log (last 24h actionable lines)

Sends a Telegram message via TELEGRAM_BOT_TOKEN to TELEGRAM_NOTIFY_CHANNEL_ID.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(os.getenv("OPENDISRUPTION_REPO", "/home/sven/OpenDisruption"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_NOTIFY_CHANNEL_ID", "").strip()


def docker_health() -> list[tuple[str, str]]:
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            text=True, timeout=15,
        )
    except Exception as exc:
        return [("docker", f"error: {exc}")]
    rows = []
    for line in out.strip().splitlines():
        name, _, status = line.partition("\t")
        if not name.startswith("kirobi-"):
            continue
        flag = "✓" if "healthy" in status or "Up" in status else "✗"
        if "unhealthy" in status:
            flag = "✗"
        rows.append((flag, f"{name}: {status[:60]}"))
    return rows


def next_priority_item() -> str:
    register = REPO / "TECH_DEBT_REGISTER.md"
    if not register.exists():
        return "(TECH_DEBT_REGISTER.md missing)"
    text = register.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in text:
        if line.strip().startswith("|") and ("P0" in line or "P1" in line):
            return line.strip()[:200]
    return "(no P0/P1 rows found)"


def recent_events(n: int = 8) -> list[str]:
    log = REPO / "kirobi-core" / "core-events.log"
    if not log.exists():
        return []
    return log.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]


def send(text: str) -> None:
    if not TOKEN or not CHAT:
        print("Telegram credentials missing", file=sys.stderr)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": CHAT,
        "text": text[:4000],
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    health = docker_health()
    healthy = sum(1 for f, _ in health if f == "✓")
    total = len(health)
    next_item = next_priority_item()
    events = recent_events()

    lines = [
        f"🤖 Hermes Daily Briefing — {now}",
        "",
        f"Services: {healthy}/{total} healthy",
    ]
    bad = [row for f, row in health if f == "✗"]
    if bad:
        lines.append("⚠ Issues:")
        lines.extend(f"  • {row}" for row in bad[:5])

    lines.append("")
    lines.append("Next priority:")
    lines.append(f"  {next_item}")

    if events:
        lines.append("")
        lines.append("Recent core-events:")
        lines.extend(f"  {e[:120]}" for e in events[-4:])

    send("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
