#!/usr/bin/env python3
"""
apk-download-history.py — Multi-Tag APK Download History Tracker
Akkumuliert wöchentliche Download-Zahlen für ALLE Release-Tags.
Milestone-Alerts pro Tag, konfigurierbar via apk-milestone-config.json.

ENV: GITHUB_REPO (default: Kirobi92/OpenDisruption)
     TELEGRAM_BOT_TOKEN
     TELEGRAM_CHAT_ID (default: 1066082496)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
REPO           = os.getenv("GITHUB_REPO", "Kirobi92/OpenDisruption")
BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID", "1066082496")
SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE   = os.path.join(SCRIPT_DIR, "apk-download-history.json")
MILESTONE_FILE = os.path.join(SCRIPT_DIR, "apk-milestone-config.json")
FIRED_FILE     = os.path.join(SCRIPT_DIR, "apk-milestone-fired.json")
MAX_WEEKS      = 52  # 1 Jahr History


def run(cmd: list) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout or r.stderr).strip()


def load_json(path: str, default) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_history() -> dict:
    return load_json(HISTORY_FILE, {"schema_version": "2.0", "tags": {}})


def load_milestone_config() -> dict:
    return load_json(MILESTONE_FILE, {"global_milestones": [5, 10, 25, 50, 100], "tag_overrides": {}})


def load_fired() -> dict:
    """Bereits gesendete Milestone-Alerts laden (Format: {tag: [milestone, ...]}). """
    return load_json(FIRED_FILE, {})


def get_all_tags() -> list[str]:
    """Alle Release-Tags aus dem GitHub-Repo abrufen."""
    rc, out = run(["gh", "release", "list", "--repo", REPO, "--limit", "50", "--json", "tagName"])
    if rc != 0 or not out:
        return []
    try:
        releases = json.loads(out)
        return [r["tagName"] for r in releases]
    except Exception:
        return []


def get_tag_downloads(tag: str) -> dict:
    """Assets + Download-Counts für einen bestimmten Tag abrufen."""
    rc, out = run(["gh", "release", "view", tag, "--repo", REPO, "--json", "assets"])
    if rc != 0 or not out:
        return {"debug": 0, "release": 0, "total": 0, "assets": []}
    try:
        data = json.loads(out)
        assets = data.get("assets", [])
        debug_dl = release_dl = 0
        asset_details = []
        for a in assets:
            name = a.get("name", "")
            count = a.get("downloadCount", 0)
            asset_details.append({"name": name, "downloads": count})
            if "debug" in name.lower():
                debug_dl += count
            elif "release" in name.lower():
                release_dl += count
        return {
            "debug": debug_dl,
            "release": release_dl,
            "total": debug_dl + release_dl,
            "assets": asset_details,
        }
    except Exception:
        return {"debug": 0, "release": 0, "total": 0, "assets": []}


def sparkline(values: list[int]) -> str:
    blocks = "▁▂▃▄▅▆▇█"
    if not values or max(values) == 0:
        return "▁" * len(values)
    vmax = max(values)
    return "".join(blocks[min(int(v / vmax * 7), 7)] for v in values)


def trend_arrow(values: list[int]) -> str:
    if len(values) < 2:
        return "–"
    delta = values[-1] - values[-2]
    if delta > 0:
        return f"↑+{delta}"
    elif delta < 0:
        return f"↓{delta}"
    return "→ ±0"


def trend_4w(values: list[int]) -> str:
    """
    Berechnet den 4-Wochen-Trend als prozentualen Zuwachs.
    Vergleicht den Durchschnitt der letzten 4 Wochen mit dem Durchschnitt
    der 4 Wochen davor (oder dem ersten verfügbaren Wert).
    """
    if len(values) < 2:
        return "–"
    recent = values[-4:]            # letzte 4 Wochen (oder weniger)
    previous = values[-8:-4]        # die 4 davor (falls vorhanden)

    avg_recent = sum(recent) / len(recent)
    if previous:
        avg_prev = sum(previous) / len(previous)
    else:
        avg_prev = values[0]  # Fallback: erster verfügbarer Wert

    if avg_prev == 0:
        return "–"
    pct = ((avg_recent - avg_prev) / avg_prev) * 100
    sign = "+" if pct >= 0 else ""
    weeks = len(recent)
    return f"{sign}{pct:.0f}% ({weeks}W)"


def send_telegram(msg: str):
    if not BOT_TOKEN:
        print("[WARN] TELEGRAM_BOT_TOKEN nicht gesetzt — kein Report gesendet")
        return
    rc, out = run([
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        "-d", f"chat_id={CHAT_ID}",
        "-d", "parse_mode=Markdown",
        "--data-urlencode", f"text={msg}",
    ])
    if rc == 0 and '"ok":true' in out:
        print("✅ Telegram gesendet")
    else:
        print(f"[WARN] Telegram-Fehler: {out[:200]}")


def check_milestones(tag: str, total: int, config: dict, fired: dict) -> list[str]:
    """
    Prüft ob neue Milestones erreicht wurden und gibt Alert-Nachrichten zurück.
    Bereits gesendete Alerts werden übersprungen (einmalig).
    """
    overrides = config.get("tag_overrides", {})
    milestones = overrides.get(tag, config.get("global_milestones", [5, 10, 25, 50, 100]))

    already_fired = set(fired.get(tag, []))
    new_alerts = []

    for m in milestones:
        if total >= m and m not in already_fired:
            new_alerts.append(f"🎉 *Milestone erreicht!* `{tag}` hat *{m}+ Downloads* 🚀\n"
                              f"Aktuelle Gesamtdownloads: *{total}*")
            already_fired.add(m)

    if new_alerts:
        fired[tag] = sorted(list(already_fired))

    return new_alerts


def main():
    now = datetime.now(timezone.utc)
    iso_week = now.strftime("%G-W%V")
    date_str = now.strftime("%Y-%m-%d")

    print(f"🔍 Starte Multi-Tag Download-History — {iso_week}")

    history = load_history()
    if "tags" not in history:
        history["tags"] = {}

    config  = load_milestone_config()
    fired   = load_fired()

    tags = get_all_tags()
    if not tags:
        print("⚠️  Keine Releases gefunden — Abbruch")
        sys.exit(0)

    print(f"📦 Gefundene Tags: {', '.join(tags)}")

    grand_total_new = 0
    milestone_alerts = []

    # ── Tag-Daten sammeln ─────────────────────────────────────────────────────
    tag_data = {}  # tag -> {stats, tag_history, totals, spark, arrow}
    for tag in tags:
        stats = get_tag_downloads(tag)
        print(f"  {tag}: debug={stats['debug']}, release={stats['release']}, total={stats['total']}")

        # Tag-History laden / initialisieren
        if tag not in history["tags"]:
            history["tags"][tag] = {"snapshots": []}

        tag_history = history["tags"][tag]["snapshots"]

        # Snapshot für diese Woche aktualisieren (deduplizieren per ISO-Woche)
        existing = next((s for s in tag_history if s["week"] == iso_week), None)
        snapshot = {
            "week": iso_week,
            "date": date_str,
            "debug_downloads": stats["debug"],
            "release_downloads": stats["release"],
            "total": stats["total"],
        }
        if existing:
            existing.update(snapshot)
        else:
            tag_history.append(snapshot)

        # Auf MAX_WEEKS begrenzen
        if len(tag_history) > MAX_WEEKS:
            history["tags"][tag]["snapshots"] = tag_history[-MAX_WEEKS:]
            tag_history = history["tags"][tag]["snapshots"]

        totals = [s["total"] for s in tag_history]
        spark  = sparkline(totals)
        arrow  = trend_arrow(totals)
        t4w    = trend_4w(totals)

        grand_total_new += stats["total"]

        tag_data[tag] = {
            "stats": stats,
            "tag_history": tag_history,
            "totals": totals,
            "spark": spark,
            "arrow": arrow,
            "trend_4w": t4w,
        }

        # ── Milestone-Check pro Tag ────────────────────────────────────────
        alerts = check_milestones(tag, stats["total"], config, fired)
        milestone_alerts.extend(alerts)

    save_json(HISTORY_FILE, history)
    save_json(FIRED_FILE, fired)
    print(f"✅ History gespeichert: {HISTORY_FILE} — {len(tags)} Tags")

    # ── Telegram-Report: Tag-Vergleich nebeneinander ──────────────────────────
    report_lines = [f"📊 *APK Download-Report — {date_str}*", ""]

    # Vergleichstabelle: alle Tags nebeneinander
    if len(tag_data) > 1:
        report_lines.append("*Tag-Vergleich:*")
        # Header-Zeile
        col_tags = list(tag_data.keys())
        header = " | ".join(f"`{t}`" for t in col_tags)
        report_lines.append(header)
        # Gesamt-Downloads pro Tag
        totals_row = " | ".join(
            f"{tag_data[t]['stats']['total']} ges." for t in col_tags
        )
        report_lines.append(totals_row)
        # Debug vs Release pro Tag
        dl_row = " | ".join(
            f"🐛{tag_data[t]['stats']['debug']} ✅{tag_data[t]['stats']['release']}" for t in col_tags
        )
        report_lines.append(dl_row)
        # Trend-Pfeile pro Tag
        trend_row = " | ".join(
            f"{tag_data[t]['spark']} {tag_data[t]['arrow']}" for t in col_tags
        )
        report_lines.append(trend_row)
        report_lines.append("")

    # Detailblock pro Tag
    report_lines.append("*Details pro Tag:*")
    for tag, d in tag_data.items():
        s = d["stats"]
        weeks_count = len(d["tag_history"])
        report_lines.append(
            f"• *{tag}* — {s['total']} gesamt | 🐛{s['debug']} ✅{s['release']} | {d['spark']} {d['arrow']} | 4W: {d['trend_4w']} ({weeks_count}W)"
        )

    report_lines.append("")
    report_lines.append(f"🏷️ *{len(tags)} Tags* | Gesamtdownloads: *{grand_total_new}*")
    if milestone_alerts:
        report_lines.append(f"🎉 {len(milestone_alerts)} neuer Milestone-Alert(s) separat gesendet")

    telegram_msg = "\n".join(report_lines)

    # Milestone-Alerts zuerst senden
    for alert in milestone_alerts:
        print(f"🎉 Milestone-Alert: {alert}")
        send_telegram(alert)

    send_telegram(telegram_msg)
    print(telegram_msg)


if __name__ == "__main__":
    main()
