#!/usr/bin/env python3
"""
Kirobi / Disruptive OS — Nächtliche Lernkonsolidierung
=======================================================
Läuft jede Nacht um 02:00 Uhr. Sammelt alle Daten des Tages,
leitet mit lokalem Ollama neue Erkenntnisse ab und speichert
diese als strukturiertes Markdown und in Qdrant.

Keine Cloud-APIs — alles 100% lokal.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent

import asyncpg
import httpx

# ── Konfiguration ──────────────────────────────────────────────────────────
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "/home/sven/OpenDisruption"))
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
QDRANT_URL = os.environ.get("QDRANT_HOST", "http://localhost:6333")
POSTGRES_DSN = (
    f"postgresql://"
    f"{os.environ.get('POSTGRES_USER','kirobi')}:"
    f"{os.environ.get('POSTGRES_PASSWORD','changeme')}@"
    f"{os.environ.get('POSTGRES_HOST','localhost')}:"
    f"{os.environ.get('POSTGRES_PORT','5432')}/"
    f"{os.environ.get('POSTGRES_DB','kirobi')}"
)
TELEGRAM_NOTIFY_URL = os.environ.get("HERMES_NOTIFY_URL", "http://localhost:9119/api/message")
TELEGRAM_USER_ID = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
CONSOLIDATION_MODEL = os.environ.get("CONSOLIDATION_MODEL", "qwen2.5:14b")
EMBED_URL = os.environ.get("EMBED_URL", "http://localhost:8004/embed")
QDRANT_COLLECTION = "kirobi_experiences"
LEARNINGS_DIR = REPO_ROOT / "experiences" / "learnings"
EVENTS_LOG = REPO_ROOT / "kirobi-core" / "core-events.log"
DRY_RUN = "--dry-run" in sys.argv

TODAY = datetime.now(timezone.utc).date()
YESTERDAY = TODAY - timedelta(days=1)
WINDOW_START = datetime.combine(YESTERDAY, datetime.min.time(), tzinfo=timezone.utc)
WINDOW_END = datetime.combine(TODAY, datetime.min.time(), tzinfo=timezone.utc)
# Naive UTC equivalents for tables that use timestamp without time zone
WINDOW_START_NAIVE = datetime.combine(YESTERDAY, datetime.min.time())
WINDOW_END_NAIVE = datetime.combine(TODAY, datetime.min.time())
DATE_LABEL = YESTERDAY.isoformat()


# ── Hilfsfunktionen ────────────────────────────────────────────────────────
def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


async def ollama_generate(prompt: str, model: str = CONSOLIDATION_MODEL, timeout: int = 300) -> str:
    """Generiert Text mit lokalem Ollama (kein Cloud-API)."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as exc:
            log(f"⚠️  Ollama-Fehler ({model}): {exc}")
            return ""


async def embed_text(text: str) -> list[float] | None:
    """Erstellt Embedding via lokalen Embeddings-Service."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(EMBED_URL, json={"text": text})
            resp.raise_for_status()
            data = resp.json()
            return data.get("embedding") or data.get("embeddings", [None])[0]
        except Exception as exc:
            log(f"⚠️  Embedding-Fehler: {exc}")
            return None


# ── Datenquellen ───────────────────────────────────────────────────────────
async def collect_conversations(pool: asyncpg.Pool) -> str:
    """Alle Nachrichten des gestrigen Tages aus PostgreSQL."""
    rows = await pool.fetch(
        """
        SELECT role, content, model_used, created_at
        FROM messages
        WHERE created_at >= $1 AND created_at < $2
        ORDER BY created_at
        """,
        WINDOW_START, WINDOW_END,
    )
    if not rows:
        return ""
    lines = [f"[{r['created_at'].strftime('%H:%M')}] {r['role'].upper()}: {r['content'][:500]}" for r in rows]
    return "\n".join(lines)


async def collect_analytics(pool: asyncpg.Pool) -> dict:
    """Analytics-Ereignisse und Modell-Nutzung des Tages."""
    model_stats = await pool.fetch(
        """
        SELECT model_used, COUNT(*) as cnt
        FROM messages
        WHERE created_at >= $1 AND created_at < $2 AND model_used IS NOT NULL
        GROUP BY model_used ORDER BY cnt DESC
        """,
        WINDOW_START, WINDOW_END,
    )
    conv_count = await pool.fetchval(
        "SELECT COUNT(*) FROM conversations WHERE created_at >= $1 AND created_at < $2",
        WINDOW_START, WINDOW_END,
    )
    task_rows = await pool.fetch(
        """
        SELECT assigned_agent, status, COUNT(*) as cnt
        FROM supervisor_tasks
        WHERE created_at >= $1 AND created_at < $2
        GROUP BY assigned_agent, status
        """,
        WINDOW_START_NAIVE, WINDOW_END_NAIVE,
    )
    return {
        "conversations": conv_count or 0,
        "models": {r["model_used"]: r["cnt"] for r in model_stats},
        "tasks": [dict(r) for r in task_rows],
    }


async def collect_audit_log(pool: asyncpg.Pool) -> list[str]:
    """Wichtige Ereignisse aus dem Audit-Log."""
    rows = await pool.fetch(
        """
        SELECT action, resource_type, details, created_at
        FROM audit_log
        WHERE created_at >= $1 AND created_at < $2
        ORDER BY created_at
        LIMIT 200
        """,
        WINDOW_START, WINDOW_END,
    )
    return [f"[{r['created_at'].strftime('%H:%M')}] {r['action']} → {r['resource_type'] or '–'}" for r in rows]


def collect_container_errors() -> dict[str, list[str]]:
    """Fehler-Logs aus allen Docker-Containern des gestrigen Tages."""
    errors: dict[str, list[str]] = {}
    since = WINDOW_START.strftime("%Y-%m-%dT%H:%M:%S")
    until = WINDOW_END.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        containers = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}"],
            text=True, timeout=10
        ).strip().split("\n")
    except Exception:
        return {}

    for cname in containers:
        if not cname:
            continue
        try:
            raw = subprocess.check_output(
                ["docker", "logs", "--since", since, "--until", until, "--tail", "200", cname],
                text=True, stderr=subprocess.STDOUT, timeout=15,
            )
            errs = [
                l.strip() for l in raw.splitlines()
                if any(kw in l.lower() for kw in ("error", "exception", "critical", "fatal", "traceback"))
            ]
            if errs:
                errors[cname] = errs[:20]
        except Exception:
            pass
    return errors


def collect_git_commits() -> list[str]:
    """Alle Git-Commits des gestrigen Tages."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log",
             f"--after={WINDOW_START.isoformat()}",
             f"--before={WINDOW_END.isoformat()}",
             "--oneline", "--no-merges"],
            text=True, timeout=10,
        )
        return [l.strip() for l in out.strip().splitlines() if l.strip()]
    except Exception:
        return []


def collect_new_inbox_files() -> list[str]:
    """Neue Dateien in sources/inbox/ (unverarbeitet)."""
    inbox = REPO_ROOT / "sources" / "inbox"
    if not inbox.exists():
        return []
    cutoff = WINDOW_START.timestamp()
    files = [
        f.name for f in inbox.iterdir()
        if f.is_file() and f.stat().st_mtime >= cutoff
    ]
    return files


def run_healthcheck() -> str:
    """Führt healthcheck.sh aus und gibt Zusammenfassung zurück."""
    script = REPO_ROOT / "infra" / "scripts" / "healthcheck.sh"
    try:
        result = subprocess.run(
            ["bash", str(script), "--quiet"],
            capture_output=True, text=True, timeout=60,
        )
        return result.stdout.strip()
    except Exception as exc:
        return f"Healthcheck-Fehler: {exc}"


def collect_core_events() -> list[str]:
    """Letzte Einträge aus kirobi-core/core-events.log des gestrigen Tages."""
    if not EVENTS_LOG.exists():
        return []
    date_prefix = f"[{YESTERDAY.strftime('%Y-%m-%d')}"
    lines = []
    try:
        with EVENTS_LOG.open() as f:
            for line in f:
                if line.startswith(date_prefix):
                    lines.append(line.strip())
    except Exception:
        pass
    return lines[-100:]


# ── Insight-Generierung via Ollama ─────────────────────────────────────────
async def generate_daily_insights(data: dict) -> dict:
    """Leitet strukturierte Erkenntnisse aus den Tagesdaten ab."""

    context = dedent(f"""
    Du bist Kirobi, ein lokales KI-Betriebssystem. Heute ist der {DATE_LABEL}.
    Analysiere die folgenden Tagesdaten und extrahiere NEUE, handlungsrelevante Erkenntnisse.

    === GESPRÄCHE ({data['analytics']['conversations']} Unterhaltungen) ===
    {data['conversations'][:3000] or 'Keine Gespräche heute.'}

    === MODELL-NUTZUNG ===
    {json.dumps(data['analytics']['models'], ensure_ascii=False)}

    === GIT-COMMITS ===
    {chr(10).join(data['commits']) or 'Keine Commits heute.'}

    === CONTAINER-FEHLER ===
    {json.dumps(data['errors'], ensure_ascii=False)[:2000] or 'Keine Fehler.'}

    === AUDIT-LOG ({len(data['audit'])} Einträge) ===
    {chr(10).join(data['audit'][:20]) or 'Keine Einträge.'}

    === NEUE DATEIEN IN INBOX ===
    {chr(10).join(data['inbox_files']) or 'Keine neuen Dateien.'}
    """).strip()

    # Drei separate Analysen für verschiedene Aspekte
    tech_prompt = context + dedent("""

    Antworte NUR auf Deutsch. Extrahiere technische Erkenntnisse:
    - Welche Fehler sind aufgetaucht? Was ist die Ursache?
    - Welche Muster gibt es in den Container-Logs?
    - Was wurde heute verbessert (Git-Commits)?
    - Welche Performance-Probleme oder Risiken erkennst du?
    - Was sollte morgen priorisiert werden?

    Format: strukturierte Aufzählungen mit konkreten Empfehlungen. Max. 400 Wörter.
    """)

    system_prompt = context + dedent("""

    Antworte NUR auf Deutsch. Analysiere die Systemnutzung:
    - Welche Modelle wurden wie oft genutzt? Was sagt das über die Präferenzen aus?
    - Welche Agenten/Services waren am aktivsten?
    - Gibt es Optimierungspotenzial bei Modellauswahl oder Routing?
    - Wie ist die allgemeine Systemgesundheit?

    Format: prägnante Erkenntnisse mit konkreten Verbesserungsvorschlägen. Max. 300 Wörter.
    """)

    conv_prompt = context + dedent("""

    Antworte NUR auf Deutsch. Analysiere die Gesprächsinhalte:
    - Welche Themen wurden heute behandelt?
    - Was hat gut funktioniert in der Kommunikation?
    - Was sollte Kirobi/Hermes morgen besser machen?
    - Welche neuen Fähigkeiten wären für den Nutzer wertvoll?

    Format: kurze, klare Erkenntnisse. Max. 300 Wörter.
    """)

    log("  🤖 Generiere technische Erkenntnisse...")
    tech = await ollama_generate(tech_prompt)
    log("  🤖 Generiere Systemanalyse...")
    system_analysis = await ollama_generate(system_prompt)
    log("  🤖 Generiere Gesprächsanalyse...")
    conv_analysis = await ollama_generate(conv_prompt) if data["conversations"] else ""

    # Kompakte Zusammenfassung für Telegram
    summary_prompt = dedent(f"""
    Fasse die wichtigsten Erkenntnisse des {DATE_LABEL} in 3-5 Sätzen zusammen.
    Schreibe als Kirobi an Sven. Nur auf Deutsch. Keine Aufzählungen, fließender Text.

    Technisch: {tech[:500]}
    System: {system_analysis[:300]}
    """).strip()

    log("  🤖 Generiere Telegram-Zusammenfassung...")
    telegram_summary = await ollama_generate(summary_prompt, model=os.environ.get("FAST_MODEL", "llama3.1:8b"))

    return {
        "tech_insights": tech,
        "system_analysis": system_analysis,
        "conv_analysis": conv_analysis,
        "telegram_summary": telegram_summary,
    }


# ── Report-Schreiber ───────────────────────────────────────────────────────
def write_markdown_report(data: dict, insights: dict) -> Path:
    """Schreibt strukturierten Markdown-Bericht in experiences/learnings/."""
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = LEARNINGS_DIR / f"nightly-{DATE_LABEL}.md"

    health_output = run_healthcheck()

    content = dedent(f"""---
zone: WORKSPACE
type: nightly-consolidation
date: {DATE_LABEL}
generated_at: {datetime.now().isoformat()}
model_used: {CONSOLIDATION_MODEL}
conversations: {data['analytics']['conversations']}
commits: {len(data['commits'])}
errors_found: {sum(len(v) for v in data['errors'].values())}
version: 1.0
---

# Nächtliche Lernkonsolidierung — {DATE_LABEL}

> Automatisch generiert von der Kirobi Nightly Consolidation Pipeline.
> Quellen: PostgreSQL, Docker-Logs, Git, Core-Events, Healthcheck.

---

## 📊 Tagesübersicht

| Metrik | Wert |
|--------|------|
| Gespräche | {data['analytics']['conversations']} |
| Nachrichten (Gesamt) | {len(data['conversations'].splitlines()) if data['conversations'] else 0} |
| Git-Commits | {len(data['commits'])} |
| Container mit Fehlern | {len(data['errors'])} |
| Neue Inbox-Dateien | {len(data['inbox_files'])} |
| Audit-Einträge | {len(data['audit'])} |

### Modell-Nutzung
{chr(10).join(f"- **{model}**: {cnt}x" for model, cnt in data['analytics']['models'].items()) or '- Keine Daten'}

### Git-Commits
{chr(10).join(f"- `{c}`" for c in data['commits']) or '- Keine Commits'}

---

## 🔧 Technische Erkenntnisse

{insights['tech_insights'] or '_Keine technischen Ereignisse heute._'}

---

## ⚙️ Systemanalyse

{insights['system_analysis'] or '_Keine Systemdaten verfügbar._'}

---

## 💬 Gesprächsanalyse

{insights['conv_analysis'] or '_Keine Gespräche heute._'}

---

## 🏥 System-Healthcheck

```
{health_output}
```

---

## ❌ Container-Fehler

{"_Keine Fehler._" if not data['errors'] else chr(10).join(
    f"### {name}\\n" + chr(10).join(f"- {e}" for e in errs)
    for name, errs in data['errors'].items()
)}

---

## 📥 Neue Inbox-Dateien

{chr(10).join(f"- `{f}`" for f in data['inbox_files']) or '_Keine neuen Dateien._'}

---

## 📋 Core-Events (Auszug)

{chr(10).join(data['core_events'][:20]) or '_Keine Events._'}

---

*Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Modell: {CONSOLIDATION_MODEL} | Lokal — kein Cloud-API*
""")

    if not DRY_RUN:
        report_path.write_text(content, encoding="utf-8")
        log(f"  📄 Report gespeichert: {report_path}")
    else:
        log(f"  📄 [DRY-RUN] Report würde gespeichert: {report_path}")

    return report_path


# ── Qdrant-Speicherung ─────────────────────────────────────────────────────
async def store_in_qdrant(report_path: Path, insights: dict) -> None:
    """Indiziert den Report-Inhalt in Qdrant für spätere RAG-Abfragen."""
    text_to_embed = f"""
Nightly Consolidation {DATE_LABEL}

Technische Erkenntnisse:
{insights['tech_insights'][:1000]}

Systemanalyse:
{insights['system_analysis'][:800]}

Gesprächsanalyse:
{insights['conv_analysis'][:600]}
""".strip()

    vector = await embed_text(text_to_embed)
    if not vector:
        log("  ⚠️  Kein Embedding verfügbar — Qdrant-Speicherung übersprungen")
        return

    payload = {
        "text": text_to_embed,
        "source": "nightly-consolidation",
        "date": DATE_LABEL,
        "file_path": str(report_path),
        "zone": "WORKSPACE",
        "type": "learning",
    }

    point_id = int(datetime.strptime(DATE_LABEL, "%Y-%m-%d").timestamp())

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.put(
                f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points",
                json={"points": [{"id": point_id, "vector": vector, "payload": payload}]},
            )
            resp.raise_for_status()
            log(f"  🗃️  In Qdrant gespeichert (Collection: {QDRANT_COLLECTION}, ID: {point_id})")
        except Exception as exc:
            log(f"  ⚠️  Qdrant-Fehler: {exc}")


# ── Telegram-Benachrichtigung ──────────────────────────────────────────────
async def send_telegram_notification(summary: str, stats: dict) -> None:
    """Sendet Zusammenfassung via Hermes an Telegram."""
    models_str = ", ".join(f"{m}:{c}x" for m, c in stats.get("models", {}).items()) or "–"
    msg = (
        f"🌙 *Nightly Report — {DATE_LABEL}*\n\n"
        f"{summary}\n\n"
        f"📊 Gespräche: {stats.get('conversations', 0)} | "
        f"Commits: {stats.get('commits', 0)} | "
        f"Fehler: {stats.get('errors', 0)}\n"
        f"🤖 Modelle: {models_str}"
    )

    if DRY_RUN:
        log(f"  📱 [DRY-RUN] Telegram-Nachricht:\n{msg}")
        return

    # Direkt über Telegram Bot API via Hermes-Config
    try:
        import configparser
        auth_file = Path("/home/sven/OpenDisruption/services/hermes-runtime/config/cli-config.yaml")
        # Telegram Bot Token aus .env
        env_file = REPO_ROOT / ".env"
        token = None
        chat_id = None
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("TELEGRAM_ALLOWED_USER_IDS="):
                    chat_id = line.split("=", 1)[1].strip().strip('"').split(",")[0]
        if token and chat_id:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                )
                if resp.status_code == 200:
                    log("  📱 Telegram-Nachricht gesendet")
                else:
                    log(f"  ⚠️  Telegram-Fehler: {resp.status_code} {resp.text[:100]}")
        else:
            log("  ⚠️  Telegram-Credentials nicht gefunden — Benachrichtigung übersprungen")
    except Exception as exc:
        log(f"  ⚠️  Telegram-Fehler: {exc}")


# ── Core-Events-Log ─────────────────────────────────────────────────────────
def log_to_core_events(stats: dict) -> None:
    """Fügt Eintrag in kirobi-core/core-events.log hinzu."""
    if DRY_RUN:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{ts}] [nightly-consolidation] ACTION: Lernkonsolidierung abgeschlossen\n"
        f"[{ts}] [nightly-consolidation] DATE: {DATE_LABEL}\n"
        f"[{ts}] [nightly-consolidation] STATS: gespräche={stats.get('conversations',0)} "
        f"commits={stats.get('commits',0)} fehler={stats.get('errors',0)}\n"
    )
    try:
        with EVENTS_LOG.open("a") as f:
            f.write(entry)
    except Exception as exc:
        log(f"  ⚠️  core-events.log Schreibfehler: {exc}")


# ── Hauptprogramm ──────────────────────────────────────────────────────────
async def main() -> None:
    log("━" * 60)
    log(f"  Kirobi Nightly Consolidation — {DATE_LABEL}")
    log(f"  Modell: {CONSOLIDATION_MODEL} | DRY-RUN: {DRY_RUN}")
    log("━" * 60)

    # 1. Daten sammeln
    log("\n📥 Daten sammeln...")
    pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=1, max_size=3)

    conversations = await collect_conversations(pool)
    analytics = await collect_analytics(pool)
    audit = await collect_audit_log(pool)
    await pool.close()

    commits = collect_git_commits()
    errors = collect_container_errors()
    inbox_files = collect_new_inbox_files()
    core_events = collect_core_events()

    log(f"  ✅ Gespräche: {analytics['conversations']}, Commits: {len(commits)}, "
        f"Fehler: {sum(len(v) for v in errors.values())}")

    data = {
        "conversations": conversations,
        "analytics": analytics,
        "audit": audit,
        "commits": commits,
        "errors": errors,
        "inbox_files": inbox_files,
        "core_events": core_events,
    }

    # 2. Erkenntnisse generieren
    log("\n🧠 Erkenntnisse generieren (lokales Ollama)...")
    insights = await generate_daily_insights(data)

    # 3. Report schreiben
    log("\n📝 Report schreiben...")
    report_path = write_markdown_report(data, insights)

    # 4. In Qdrant speichern
    log("\n🗃️  In Qdrant indizieren...")
    if not DRY_RUN:
        await store_in_qdrant(report_path, insights)

    # 5. Telegram-Benachrichtigung
    log("\n📱 Telegram-Benachrichtigung senden...")
    stats = {
        "conversations": analytics["conversations"],
        "commits": len(commits),
        "errors": sum(len(v) for v in errors.values()),
        "models": analytics["models"],
    }
    await send_telegram_notification(insights["telegram_summary"], stats)

    # 6. Core-Events-Log
    log_to_core_events(stats)

    log("\n" + "━" * 60)
    log(f"  ✅ Nightly Consolidation abgeschlossen — {DATE_LABEL}")
    log("━" * 60)


if __name__ == "__main__":
    asyncio.run(main())
