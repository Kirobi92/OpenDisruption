#!/usr/bin/env python3
"""
sc-trend-sync.py
================
Liest SC_ISSUE_COUNT aus den letzten lint-workflows.yml CI-Runs via GitHub API
und speichert eine historische Trend-Kurve in sc-trend.json.

Aufruf:
  python3 sc-trend-sync.py

Benötigte ENV:
  GITHUB_TOKEN   — Personal Access Token mit repo-Scope (oder gh CLI auth)
  GITHUB_REPO    — z.B. "Kirobi92/OpenDisruption" (optional, Auto-Detect via git)

Ausgabe:
  scripts/sc-trend.json — historischer SC-Count je CI-Run (max. 20 Einträge)

Integration:
  - Wird von /api/dashboard in server.py als sc_trend Block eingebunden
  - Kann via cron/systemd nach jedem lint-CI-Run aufgerufen werden
  - Läuft auch lokal ohne laufenden Server
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SC_TREND_FILE = SCRIPT_DIR / "sc-trend.json"
SC_ALERT_HISTORY_FILE = SCRIPT_DIR / "sc-alert-history.json"
MAX_ENTRIES = 20
MAX_ALERT_ENTRIES = 100
WORKFLOW_NAME = "Lint GitHub Actions Workflows"


def get_github_repo() -> str:
    """Auto-Detect GitHub Repo aus git-Remote oder ENV."""
    repo = os.environ.get("GITHUB_REPO", "")
    if repo:
        return repo
    try:
        result = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True,
            cwd=str(SCRIPT_DIR.parent.parent),
        )
        url = result.stdout.strip()
        # https://github.com/Kirobi92/OpenDisruption.git → Kirobi92/OpenDisruption
        if "github.com" in url:
            parts = url.split("github.com/")[-1]
            repo = parts.removesuffix(".git")
            return repo
    except Exception:
        pass
    return "Kirobi92/OpenDisruption"


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        # gh CLI Auth
        try:
            result = subprocess.check_output(
                ["gh", "auth", "token"], capture_output=True, text=True
            )
            token = result.stdout.strip()
        except Exception:
            pass
    return token


def fetch_runs(repo: str, token: str, limit: int = 20) -> list:
    """Holt die letzten lint-CI-Runs via GitHub API."""
    import urllib.request
    url = (
        f"https://api.github.com/repos/{repo}/actions/workflows"
        f"?per_page=20"
    )
    # Erst Workflow-ID ermitteln
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[WARN] Konnte Workflows nicht abrufen: {e}")
        return []

    workflow_id = None
    for wf in data.get("workflows", []):
        if "lint" in wf.get("name", "").lower() or "lint-workflows" in wf.get("path", ""):
            workflow_id = wf["id"]
            break

    if not workflow_id:
        print("[WARN] lint-workflows.yml Workflow-ID nicht gefunden")
        return []

    # Runs für diesen Workflow
    runs_url = (
        f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/runs"
        f"?per_page={limit}&branch=main"
    )
    req2 = urllib.request.Request(runs_url)
    req2.add_header("Authorization", f"Bearer {token}")
    req2.add_header("Accept", "application/vnd.github.v3+json")
    req2.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req2, timeout=15) as resp:
            runs_data = json.loads(resp.read())
    except Exception as e:
        print(f"[WARN] Konnte Runs nicht abrufen: {e}")
        return []

    return runs_data.get("workflow_runs", [])


def extract_sc_count_from_run_via_gh(token: str, run_id: int) -> int | None:
    """Liest sc_issue_count aus den CI-Logs via gh CLI."""
    try:
        # gh muss im Git-Repo-Verzeichnis aufgerufen werden
        repo_dir = "/home/sven/OpenDisruption"
        if not Path(repo_dir).exists():
            repo_dir = str(Path(__file__).parent.parent.parent.parent)  # Fallback
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--log"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GH_TOKEN": token},
            cwd=repo_dir,
        )
        log_text = result.stdout
        import re
        for line in log_text.splitlines():
            if "sc_issue_count=" in line:
                # Bereinige ANSI-Escape-Sequenzen + letztes Token
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                token_part = clean_line.rsplit(None, 1)[-1].strip()
                if token_part.startswith("sc_issue_count="):
                    try:
                        val = int(token_part.split("=")[1])
                        return val
                    except ValueError:
                        pass
    except Exception:
        pass
    return None


def extract_sc_count_from_run(repo: str, token: str, run_id: int) -> int | None:
    """Liest sc_issue_count aus den Job-Outputs eines CI-Runs."""
    # Zuerst via gh CLI versuchen (schneller, folgt Redirects)
    result_gh = extract_sc_count_from_run_via_gh(token, run_id)
    if result_gh is not None:
        return result_gh

    import urllib.request

    # Jobs des Runs abrufen
    jobs_url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
    req = urllib.request.Request(jobs_url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            jobs_data = json.loads(resp.read())
    except Exception as e:
        print(f"[WARN] Konnte Jobs für Run {run_id} nicht abrufen: {e}")
        return None

    for job in jobs_data.get("jobs", []):
        for step in job.get("steps", []):
            # Wir suchen den Output via Logs
            if "shellcheck" in step.get("name", "").lower():
                # Logs des Steps lesen
                logs_url = f"https://api.github.com/repos/{repo}/actions/jobs/{job['id']}/logs"
                req2 = urllib.request.Request(logs_url)
                req2.add_header("Authorization", f"Bearer {token}")
                req2.add_header("Accept", "application/vnd.github.v3+json")
                try:
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        log_text = resp2.read().decode("utf-8", errors="replace")
                    # Suche nach "sc_issue_count=N" (Output-Zeile)
                    for line in log_text.splitlines():
                        stripped = line.split(" ")[-1].strip() if " " in line else line.strip()
                        if stripped.startswith("sc_issue_count="):
                            try:
                                return int(stripped.split("=")[1])
                            except ValueError:
                                pass
                except Exception:
                    pass
    return None


def load_trend() -> list:
    if SC_TREND_FILE.exists():
        try:
            return json.loads(SC_TREND_FILE.read_text())
        except Exception:
            pass
    return []


def save_trend(data: list) -> None:
    SC_TREND_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )


def load_alert_history() -> list:
    if SC_ALERT_HISTORY_FILE.exists():
        try:
            return json.loads(SC_ALERT_HISTORY_FILE.read_text())
        except Exception:
            pass
    return []


def save_alert_history(data: list) -> None:
    SC_ALERT_HISTORY_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )


def record_alert_event(run_id: int, sc_count: int, threshold: int, started_at: str) -> dict:
    """Trägt ein SC-Alert-Event in sc-alert-history.json ein (Audit-Trail)."""
    alert_history = load_alert_history()
    existing_ids = {e.get("run_id") for e in alert_history}
    if run_id in existing_ids:
        return {}  # Bereits gespeichert
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "run_started_at": started_at,
        "sc_issue_count": sc_count,
        "threshold": threshold,
        "delta": sc_count - threshold,
    }
    alert_history.append(event)
    if len(alert_history) > MAX_ALERT_ENTRIES:
        alert_history = alert_history[-MAX_ALERT_ENTRIES:]
    save_alert_history(alert_history)
    print(f"[ALERT] SC-Alert eingetragen: run_id={run_id}, sc_issue_count={sc_count} > threshold={threshold}")
    return event


def sync() -> dict:
    """Hauptfunktion: Sync SC-Trend aus GitHub API."""
    repo = get_github_repo()
    token = get_github_token()

    if not token:
        print("[ERROR] Kein GitHub-Token gefunden. Bitte GITHUB_TOKEN setzen oder `gh auth login`.")
        sys.exit(1)

    # SC-Alert-Schwelle aus ENV lesen (Standard 0 = jede Finding löst Alert aus)
    try:
        sc_threshold = int(os.environ.get("KIROBI_SC_ALERT_THRESHOLD", "0"))
    except ValueError:
        sc_threshold = 0

    print(f"[INFO] Sync SC-Trend für Repo: {repo}")
    runs = fetch_runs(repo, token, limit=20)
    if not runs:
        print("[WARN] Keine CI-Runs gefunden.")
        return {}

    trend = load_trend()
    existing_ids = {e["run_id"] for e in trend}

    new_entries = 0
    new_alerts = 0
    for run in runs:
        run_id = run["id"]
        if run_id in existing_ids:
            continue
        if run.get("conclusion") not in ("success", "failure"):
            continue  # Skip pending/in_progress

        sc_count = extract_sc_count_from_run(repo, token, run_id)
        entry = {
            "run_id": run_id,
            "started_at": run.get("created_at", ""),
            "conclusion": run.get("conclusion", "unknown"),
            "sc_issue_count": sc_count if sc_count is not None else -1,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        trend.append(entry)
        existing_ids.add(run_id)
        new_entries += 1
        print(f"[OK]  Run {run_id}: sc_issue_count={sc_count}, conclusion={run.get('conclusion')}")

        # Alert-Event eintragen wenn sc_count > threshold
        if sc_count is not None and sc_count > sc_threshold:
            alert_event = record_alert_event(
                run_id=run_id,
                sc_count=sc_count,
                threshold=sc_threshold,
                started_at=run.get("created_at", ""),
            )
            if alert_event:
                new_alerts += 1

    # Sortieren nach Zeit (älteste zuerst), max. MAX_ENTRIES behalten
    trend.sort(key=lambda x: x.get("started_at", ""))
    if len(trend) > MAX_ENTRIES:
        trend = trend[-MAX_ENTRIES:]

    save_trend(trend)

    # Zusammenfassung
    valid = [e for e in trend if e["sc_issue_count"] >= 0]
    alert_history = load_alert_history()
    summary = {
        "entries": len(trend),
        "new_this_sync": new_entries,
        "new_alerts_this_sync": new_alerts,
        "total_alerts": len(alert_history),
        "latest_alert": alert_history[-1] if alert_history else None,
        "latest_count": valid[-1]["sc_issue_count"] if valid else None,
        "trend_direction": None,
        "avg_last_5": None,
    }
    if len(valid) >= 2:
        counts = [e["sc_issue_count"] for e in valid]
        delta = counts[-1] - counts[0]
        summary["trend_direction"] = "▲" if delta > 0 else ("▼" if delta < 0 else "→")
        summary["avg_last_5"] = round(sum(counts[-5:]) / min(5, len(counts)), 2)

    print(f"[INFO] Trend-Datei aktualisiert: {SC_TREND_FILE} ({len(trend)} Einträge, {new_entries} neu)")
    return summary


if __name__ == "__main__":
    result = sync()
    if result:
        print(json.dumps(result, indent=2))
