#!/usr/bin/env python3
"""
Hermes Self-Improvement Loop.

Runs nightly; for each next P0/P1 item in TECH_DEBT_REGISTER.md:
  1. Verifies repo gate (`make integration-test`)
  2. Detects the next actionable item not yet marked done
  3. Sends a Telegram suggestion with a one-line plan
  4. (Optional) opens a draft GitHub issue via `gh` CLI if HERMES_AUTO_ISSUE=1

This script does NOT auto-modify code. Sven approves before Hermes refactors.
"""
from __future__ import annotations

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
AUTO_ISSUE = os.getenv("HERMES_AUTO_ISSUE", "0") == "1"


def telegram(text: str) -> None:
    if not TOKEN or not CHAT:
        print("[skip telegram] missing token/chat", file=sys.stderr)
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT, "text": text[:4000],
        "disable_web_page_preview": "true",
    }).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=20).read()
    except Exception as exc:
        print(f"[telegram error] {exc}", file=sys.stderr)


def run_gate() -> tuple[bool, str]:
    try:
        out = subprocess.run(
            ["make", "integration-test"],
            cwd=REPO, capture_output=True, text=True, timeout=600,
        )
        ok = out.returncode == 0
        tail = (out.stdout + out.stderr).strip().splitlines()[-15:]
        return ok, "\n".join(tail)
    except Exception as exc:
        return False, f"gate failed to run: {exc}"


def next_item() -> str | None:
    reg = REPO / "TECH_DEBT_REGISTER.md"
    if not reg.exists():
        return None
    for line in reg.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s.startswith("|") and ("P0" in s or "P1" in s) and "done" not in s.lower():
            return s[:300]
    return None


def maybe_open_issue(item: str) -> None:
    if not AUTO_ISSUE:
        return
    title = f"[hermes-auto] Next: {item.split('|')[1].strip() if '|' in item else item[:60]}"
    body = f"Auto-detected next priority by hermes self_improve loop.\n\n```\n{item}\n```\n\nRun `make integration-test` first; reference TECH_DEBT_REGISTER.md."
    try:
        subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body, "--label", "hermes-auto"],
            cwd=REPO, check=True, timeout=30,
        )
    except Exception as exc:
        print(f"[gh issue create failed] {exc}", file=sys.stderr)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ok, tail = run_gate()
    item = next_item()

    msg = [
        f"🔁 Hermes Self-Improve — {now}",
        "",
        f"Gate (make integration-test): {'✓ PASS' if ok else '✗ FAIL'}",
    ]
    if not ok:
        msg.append("Last lines:")
        msg.extend(f"  {ln[:120]}" for ln in tail.splitlines()[-6:])

    if item:
        msg.extend(["", "Next priority candidate:", f"  {item}"])
        if AUTO_ISSUE:
            maybe_open_issue(item)
            msg.append("→ GH issue opened (hermes-auto label)")
        else:
            msg.append("(set HERMES_AUTO_ISSUE=1 to auto-open issues)")
    else:
        msg.append("✓ No P0/P1 backlog items left.")

    telegram("\n".join(msg))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
