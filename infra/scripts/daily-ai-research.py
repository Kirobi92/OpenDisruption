#!/usr/bin/env python3
"""
Kirobi / Disruptive OS — Tägliche KI-Forschung & Optimierungsanalyse
======================================================================
Läuft jeden Morgen um 07:00 Uhr.
Sucht im Web nach Neuigkeiten im KI-Agenten-Space, vergleicht mit
unserem Setup und bewertet ob eine Integration sich lohnt.

Quellen:
  - DuckDuckGo-Suche (kein API-Key nötig)
  - RSS-Feeds (HuggingFace, LangChain, GitHub Blog, Dev.to)
  - GitHub Trending API (keine Auth nötig)
  - GitHub Topics (ai-agents, llm, autonomous-agents)

Ausgabe:
  - Markdown-Report unter experiences/learnings/ai-research-YYYY-MM-DD.md
  - Telegram-Morgenbriefing (Top-5 Erkenntnisse)
  - Qdrant-Indexierung für spätere Abfragen
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent

import feedparser
import httpx

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# ── Konfiguration ──────────────────────────────────────────────────────────
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "/home/sven/OpenDisruption"))
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
QDRANT_URL = os.environ.get("QDRANT_HOST", "http://localhost:6333")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = [
    cid.strip()
    for cid in os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
    if cid.strip()
]

OLLAMA_MODEL = os.environ.get("RESEARCH_MODEL", "qwen2.5:14b")
FAST_MODEL = os.environ.get("FAST_MODEL", "llama3.1:8b")

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
REPORT_PATH = REPO_ROOT / "experiences" / "learnings" / f"ai-research-{TODAY}.md"
EVENTS_LOG = REPO_ROOT / "kirobi-core" / "core-events.log"

# ── Unser aktuelles Setup (Vergleichsbasis) ────────────────────────────────
OUR_STACK = """
AKTUELLES KIROBI/OPENDISRUPTION SETUP:
- Hermes-Agent (lokaler AI-Gateway, Telegram, Cron, Orchestrierung)
- Ollama (lokale LLMs: qwen2.5:14b, llama3.1:8b, llama3.2-vision, nomic-embed-text)
- GitHub Models API (gpt-4.1, gpt-4.1-mini, gpt-4o als Cloud-Fallback)
- Qdrant (Vektor-Datenbank, 7 Collections)
- PostgreSQL (Relationale DB, Row-Level Security)
- Next.js 15 (PWA, Admin-Dashboard, Voice-Interface)
- FastAPI (8 Python-Microservices: auth, api, embeddings, ingest, retrieval, model-routing...)
- Caddy (Reverse Proxy, mDNS/Tailscale)
- MCP (Model Context Protocol: Memory, Sequential-Thinking, Filesystem, Postgres)
- Docker Compose (23 Services, lokal auf x86 Server)
- Nightly Consolidation (nächtliche Lernverarbeitung mit Ollama + Qdrant)
- Systemd Timer (Cron-Ersatz für nightly tasks)

GEPLANT/IN ARBEIT:
- LiteLLM (Provider-Abstraction)
- Temporal oder LangGraph (Orchestrierung)
- OpenFGA + OPA (Policy-Engine)
- Langfuse + OpenLIT (Observability)
- Honcho (Multi-User Memory)
"""

# ── RSS Feed Quellen ───────────────────────────────────────────────────────
RSS_FEEDS = [
    ("HuggingFace Blog", "https://huggingface.co/blog/feed.xml"),
    ("LangChain Blog", "https://blog.langchain.dev/rss/"),
    ("GitHub Blog (AI)", "https://github.blog/feed/"),
    ("Dev.to AI Tag", "https://dev.to/feed/tag/ai"),
    ("The Batch (deeplearning.ai)", "https://www.deeplearning.ai/the-batch/feed/"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/"),
]

# ── DuckDuckGo Suchanfragen ────────────────────────────────────────────────
DDG_QUERIES = [
    "AI agent framework 2026 new release",
    "local LLM orchestration tool open source 2026",
    "autonomous AI agent self-improving 2026",
    "MCP model context protocol tools 2026",
    "Ollama alternative local inference 2026",
    "AI memory system personal assistant 2026",
    "multi-agent system open source May 2026",
    "LLM routing optimization 2026",
]

# ── GitHub Topics ──────────────────────────────────────────────────────────
GITHUB_TOPICS = ["ai-agents", "autonomous-agents", "llm-agent", "local-ai"]


# ── Hilfsfunktionen ────────────────────────────────────────────────────────

async def ollama_generate(prompt: str, model: str = OLLAMA_MODEL, timeout: int = 180) -> str:
    """Lokale Ollama-Generierung."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


async def send_telegram(text: str) -> None:
    """Telegram-Nachricht an alle erlaubten Chats senden."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_IDS:
        print("  [telegram] Kein Token/Chat-ID konfiguriert — übersprungen")
        return
    async with httpx.AsyncClient(timeout=30) as client:
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )
                print(f"  [telegram] Gesendet an {chat_id}")
            except Exception as e:
                print(f"  [telegram] Fehler bei {chat_id}: {e}")


def log_event(message: str) -> None:
    """In core-events.log schreiben."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [daily-ai-research] {message}\n"
    try:
        with open(EVENTS_LOG, "a") as f:
            f.write(entry)
    except Exception:
        pass
    print(f"  [log] {message}")


# ── Datensammlung ──────────────────────────────────────────────────────────

def fetch_ddg_results() -> list[dict]:
    """DuckDuckGo-Suche für alle Anfragen."""
    results = []
    print("  [ddg] Starte Web-Suche...")
    with DDGS() as ddgs:
        for query in DDG_QUERIES:
            try:
                hits = list(ddgs.text(query, max_results=5, timelimit="w"))  # letzte Woche
                for h in hits:
                    results.append({
                        "source": "duckduckgo",
                        "query": query,
                        "title": h.get("title", ""),
                        "url": h.get("href", ""),
                        "snippet": h.get("body", "")[:400],
                    })
                print(f"  [ddg] '{query[:40]}' → {len(hits)} Treffer")
            except Exception as e:
                print(f"  [ddg] Fehler bei '{query[:40]}': {e}")
    return results


def fetch_rss_feeds() -> list[dict]:
    """RSS-Feeds der letzten 48h abrufen."""
    results = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    print("  [rss] Lese Feeds...")
    for feed_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries[:20]:
                # Datum ermitteln
                pub = None
                for attr in ("published_parsed", "updated_parsed"):
                    if hasattr(entry, attr) and getattr(entry, attr):
                        import calendar
                        pub = datetime.fromtimestamp(
                            calendar.timegm(getattr(entry, attr)), tz=timezone.utc
                        )
                        break
                if pub and pub < cutoff:
                    continue
                results.append({
                    "source": "rss",
                    "feed": feed_name,
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "snippet": re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:400],
                })
                count += 1
            print(f"  [rss] {feed_name}: {count} neue Einträge")
        except Exception as e:
            print(f"  [rss] Fehler bei {feed_name}: {e}")
    return results


async def fetch_github_trending() -> list[dict]:
    """GitHub-Repos nach Topics der letzten 7 Tage abrufen."""
    results = []
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    async with httpx.AsyncClient(timeout=30) as client:
        for topic in GITHUB_TOPICS:
            try:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    params={
                        "q": f"topic:{topic} created:>{since}",
                        "sort": "stars",
                        "order": "desc",
                        "per_page": 5,
                    },
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for repo in items:
                        results.append({
                            "source": "github",
                            "topic": topic,
                            "name": repo.get("full_name", ""),
                            "url": repo.get("html_url", ""),
                            "stars": repo.get("stargazers_count", 0),
                            "description": repo.get("description", "")[:300],
                            "language": repo.get("language", ""),
                        })
                    print(f"  [github] Topic '{topic}': {len(items)} neue Repos")
            except Exception as e:
                print(f"  [github] Fehler bei Topic '{topic}': {e}")
    return results


# ── Analyse ────────────────────────────────────────────────────────────────

async def analyze_with_ollama(all_findings: list[dict]) -> dict:
    """Ollama analysiert die Findings und vergleicht mit unserem Stack."""
    # Kompaktes JSON für den Prompt
    findings_text = ""
    for i, f in enumerate(all_findings[:60], 1):  # max 60 Einträge
        if f["source"] == "github":
            findings_text += f"{i}. [GitHub ⭐{f['stars']}] {f['name']}: {f['description']} | {f['url']}\n"
        elif f["source"] == "rss":
            findings_text += f"{i}. [RSS/{f['feed']}] {f['title']}: {f['snippet'][:200]} | {f['url']}\n"
        else:
            findings_text += f"{i}. [Web] {f['title']}: {f['snippet'][:200]} | {f['url']}\n"

    # Haupt-Analyse
    analysis_prompt = dedent(f"""
    Du bist ein KI-Architekt für das Kirobi/OpenDisruption System.
    Heute ist {TODAY}.

    {OUR_STACK}

    NEUESTE FINDINGS AUS DEM KI-AGENTEN-SPACE (letzte 7 Tage):
    {findings_text}

    Analysiere diese Findings und erstelle einen strukturierten deutschen Bericht:

    ## 1. TOP 5 RELEVANTE NEUIGKEITEN
    (Was ist wirklich neu und wichtig? Sortiert nach Relevanz für unser Setup)

    ## 2. KONKRETE OPTIMIERUNGSVORSCHLÄGE
    (Welche Tools/Ansätze könnten unser System verbessern? Mit Begründung)
    Format: **[HOCH/MITTEL/NIEDRIG]** Tool/Technik: Warum es sich lohnt

    ## 3. RISIKEN & VERALTETES
    (Welche unserer aktuellen Technologien werden möglicherweise von besseren ersetzt?)

    ## 4. SOFORT-AKTIONEN (diese Woche umsetzbar)
    (Max. 3 konkrete, kleine Verbesserungen die wenig Zeit kosten)

    ## 5. FAZIT IN 3 SÄTZEN
    (Was ist der wichtigste Take-Away heute?)

    Sei direkt, konkret und ehrlich. Kein Marketing-Sprech.
    """).strip()

    print("  [ollama] Starte Hauptanalyse...")
    analysis = await ollama_generate(analysis_prompt, model=OLLAMA_MODEL, timeout=240)

    # Kurze Telegram-Zusammenfassung
    summary_prompt = dedent(f"""
    Fasse diesen KI-Forschungsbericht für Sven in max. 5 Telegram-Nachrichten-Punkte zusammen.
    Jeder Punkt max. 2 Zeilen. Deutsch. Direkt. Keine Floskeln.
    Format: Emoji + kurzer Titel + 1-Satz-Beschreibung

    BERICHT:
    {analysis[:2000]}
    """).strip()

    print("  [ollama] Erstelle Telegram-Zusammenfassung...")
    summary = await ollama_generate(summary_prompt, model=FAST_MODEL, timeout=60)

    return {"analysis": analysis, "summary": summary}


# ── Qdrant Indexierung ─────────────────────────────────────────────────────

async def index_to_qdrant(report_text: str) -> None:
    """Bericht in Qdrant kirobi_experiences indexieren."""
    embed_url = os.environ.get("EMBEDDINGS_HOST", "http://localhost:8004")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Embedding holen
            resp = await client.post(
                f"{embed_url}/embed",
                json={"text": report_text[:2000]},
            )
            if resp.status_code != 200:
                print(f"  [qdrant] Embedding-Fehler: {resp.status_code}")
                return
            vector = resp.json().get("embedding", [])
            if not vector:
                return

            # In Qdrant speichern
            point_id = int(datetime.now(timezone.utc).timestamp())
            qdrant_resp = await client.put(
                f"{QDRANT_URL}/collections/kirobi_experiences/points",
                json={
                    "points": [{
                        "id": point_id,
                        "vector": vector,
                        "payload": {
                            "type": "ai_research",
                            "date": TODAY,
                            "source": "daily-ai-research",
                            "zone": "WORKSPACE",
                            "content": report_text[:1000],
                        },
                    }]
                },
            )
            if qdrant_resp.status_code in (200, 206):
                print(f"  [qdrant] Indexiert (ID: {point_id})")
            else:
                print(f"  [qdrant] Fehler: {qdrant_resp.status_code}")
    except Exception as e:
        print(f"  [qdrant] Fehler: {e}")


# ── Hauptprogramm ──────────────────────────────────────────────────────────

async def main() -> None:
    start = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  Kirobi Daily AI Research — {TODAY}")
    print(f"{'='*60}\n")

    # ── 1. Daten sammeln ──────────────────────────────────────────────────
    print("[ 1/4 ] Daten sammeln...")
    ddg_results = fetch_ddg_results()
    rss_results = fetch_rss_feeds()
    github_results = await fetch_github_trending()

    all_findings = ddg_results + rss_results + github_results
    print(f"  Gesamt: {len(all_findings)} Findings ({len(ddg_results)} Web, "
          f"{len(rss_results)} RSS, {len(github_results)} GitHub)\n")

    # ── 2. Analyse ────────────────────────────────────────────────────────
    print("[ 2/4 ] KI-Analyse mit Ollama...")
    if not all_findings:
        print("  Keine Findings — überspringe Analyse")
        return

    analysis_result = await analyze_with_ollama(all_findings)
    print()

    # ── 3. Bericht schreiben ──────────────────────────────────────────────
    print("[ 3/4 ] Bericht schreiben...")
    duration = (datetime.now(timezone.utc) - start).seconds
    sources_md = "\n".join(
        f"- [{f.get('title') or f.get('name', 'Unbekannt')}]({f.get('url', '#')})"
        for f in all_findings[:20]
        if f.get("url")
    )

    report = dedent(f"""---
zone: WORKSPACE
created_by: daily-ai-research
date: {TODAY}
sources: {len(all_findings)}
duration_seconds: {duration}
---

# KI-Forschungsbericht — {TODAY}

> Täglich um 07:00 automatisch generiert. Vergleicht Neuigkeiten im KI-Agenten-Space
> mit dem Kirobi/OpenDisruption Setup und bewertet Optimierungspotenziale.

## Analyse

{analysis_result["analysis"]}

---

## Quellen ({len(all_findings)} Findings)

{sources_md}

---
*Generiert von `infra/scripts/daily-ai-research.py` | Modell: {OLLAMA_MODEL}*
""").strip()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"  Bericht: {REPORT_PATH}")

    # ── 4. Benachrichtigungen ─────────────────────────────────────────────
    print("[ 4/4 ] Telegram-Briefing senden...")
    telegram_msg = (
        f"🔬 <b>Kirobi KI-Forschung — {TODAY}</b>\n\n"
        f"{analysis_result['summary']}\n\n"
        f"📄 Vollbericht: <code>experiences/learnings/ai-research-{TODAY}.md</code>\n"
        f"📊 {len(all_findings)} Quellen • {len(ddg_results)} Web • "
        f"{len(rss_results)} RSS • {len(github_results)} GitHub"
    )
    await send_telegram(telegram_msg)

    # Qdrant
    await index_to_qdrant(analysis_result["analysis"])

    # Core Events Log
    log_event(f"Tägliche KI-Forschung abgeschlossen: {len(all_findings)} Findings, "
              f"Bericht: {REPORT_PATH.name}")

    elapsed = (datetime.now(timezone.utc) - start).seconds
    print(f"\n✅ Fertig in {elapsed}s\n")


if __name__ == "__main__":
    asyncio.run(main())
