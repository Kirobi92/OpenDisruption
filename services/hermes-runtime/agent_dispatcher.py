#!/usr/bin/env python3
"""
agent_dispatcher.py — Hermes Agent-Dispatcher

Hermes ruft dieses Script über das terminal-Tool auf, um alle registrierten
OpenDisruption-Agenten zu delegieren.

Verwendung:
    python3 /home/sven/OpenDisruption/services/hermes-runtime/agent_dispatcher.py \
        --agent hermes-reasoner \
        --task chain_of_thought \
        --payload '{"question": "Welche Services laufen?"}'

Verfügbare Agenten:
    hermes-reasoner   – Reasoning, Chain-of-Thought, Dokument-Klassifizierung
    obsidian          – Obsidian-Vault lesen/schreiben, Daily Notes, MOC
    openclaw          – Web-Fetch, API-Calls, Browser-Automation
    opencode          – Code generieren, debuggen, Refactoring
    kirobi-core       – Status, Backlog, Scan via kirobi_core CLI
    supervisor        – Task-Steuerung über HTTP-API des Supervisors
    ingest            – Dokument-Ingestion über HTTP-API
    retrieval         – RAG-Suche, Knowledge-Retrieval
    analytics         – Event-Tracking, Stats

Zone: WORKSPACE
Autor: Hermes / Copilot
Version: 1.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any

REPO_ROOT = Path("/home/sven/OpenDisruption")
sys.path.insert(0, str(REPO_ROOT))

# Inject Hermes venv site-packages so agents can use httpx, pydantic etc.
_HERMES_VENV_SITE = Path("/opt/hermes/.venv/lib/python3.13/site-packages")
if _HERMES_VENV_SITE.exists() and str(_HERMES_VENV_SITE) not in sys.path:
    sys.path.insert(1, str(_HERMES_VENV_SITE))


# ─── HTTP-basierte Agenten ────────────────────────────────────────────────────
# Docker-interne URLs (Service-DNS-Name + interner Port, nicht der Host-Port).
# Alle Services liegen im kirobi-net Netzwerk — 127.0.0.1 ist der Container-Loopback,
# nicht der Host. Externe Host-Ports (z.B. 8007→8000) gelten nicht im Container.

HTTP_AGENTS = {
    "ingest":           "http://ingest:8000",           # Host: 8007→8000
    "retrieval":        "http://retrieval:8000",        # Host: 8006→8000
    "analytics":        "http://analytics:8010",        # Host: 8010→8010
    "embeddings":       "http://embeddings:8000",       # Host: 8004→8000
    "auth":             "http://auth:8000",             # Host: 8002→8000
    "api":              "http://api:8000",              # Host: 8003→8000
    "model-routing":    "http://model-routing:8009",    # Host: 8009→8009
    "voice":            "http://voice-processing:8001", # Host: 8001→8001
    "image-generation": "http://image-generation:8011", # Host: 8011→8011
    "music-generation": "http://music-generation:8013", # Host: 8013→8013
    "video-generation": "http://video-generation:8014", # Host: 8014→8014
    "media-processing": "http://media-processing:8012", # Host: 8012→8012
    "nutzi":            "http://nutzi:8015",            # Host: 8016→8015
}


def call_http_agent(agent_name: str, task_type: str, payload: dict) -> dict:
    """Ruft einen HTTP-Service-Agenten auf."""
    import urllib.request
    import urllib.error

    base_url = HTTP_AGENTS[agent_name]

    # Standard-Endpunkte je nach task_type
    endpoint_map = {
        "health": "/health",
        "ingest": "/ingest",
        "search": "/search",
        "rag": "/rag",
        "embed": "/embed",
        "stats": "/stats",
        "generate": "/generate",
        "transcribe": "/transcribe",
        "synthesize": "/synthesize",
        "tts": "/synthesize",
        "stt": "/transcribe",
        "ask": "/ask",
        "topics": "/topics",
        "modules": "/modules",
        "artikelstamm": "/artikelstamm/guide",
    }
    endpoint = endpoint_map.get(task_type, f"/{task_type}")
    url = f"{base_url}{endpoint}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if payload else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"success": False, "error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


# ─── Python-Agenten ───────────────────────────────────────────────────────────

def call_python_agent(agent_name: str, task_type: str, payload: dict, zone: str = "WORKSPACE") -> dict:
    """Importiert und ruft einen Python-BaseAgent auf."""
    try:
        from agents._base.agent import Task

        if agent_name in ("hermes-reasoner", "hermes"):
            import os
            # Ensure OLLAMA_HOST is set (agent uses this, not OLLAMA_BASE_URL)
            if "OLLAMA_HOST" not in os.environ:
                os.environ["OLLAMA_HOST"] = "http://ollama:11434"
            # Set full model tag if only base name given
            if "OLLAMA_MODEL" not in os.environ:
                os.environ["OLLAMA_MODEL"] = "qwen2.5:14b"
            from agents.hermes.agent import HermesReasonerAgent
            agent = HermesReasonerAgent()
        elif agent_name == "obsidian":
            from agents.obsidian.agent import ObsidianAgent
            vault_path = str(REPO_ROOT / "obsidian")
            agent = ObsidianAgent(vault_path=vault_path)
        elif agent_name == "openclaw":
            from agents.openclaw.agent import OpenClawAgent
            agent = OpenClawAgent()
        elif agent_name == "opencode":
            from agents.opencode.agent import OpenCodeAgent
            agent = OpenCodeAgent()
        else:
            return {"success": False, "error": f"Unbekannter Python-Agent: {agent_name}"}

        task = Task(task_type=task_type, zone=zone, payload=payload)
        result = agent.run(task)

        return {
            "success": result.success,
            "agent_id": result.agent_id,
            "task_type": task_type,
            "payload": result.payload,
            "error": result.error,
            "confidence": result.confidence,
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Import-Fehler: {e}. Führe kirobi_core direkt aus.",
            "agent": agent_name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(),
        }


# ─── kirobi_core CLI ─────────────────────────────────────────────────────────

def call_kirobi_core(task_type: str, payload: dict) -> dict:
    """Ruft kirobi_core CLI-Befehle auf."""
    cmd_map = {
        "status": ["python3", "-m", "kirobi_core", "status", "--json"],
        "backlog": ["python3", "-m", "kirobi_core", "backlog", "--limit", str(payload.get("limit", 10))],
        "scan": ["python3", "-m", "kirobi_core", "scan"],
        "doctor": ["python3", "-m", "kirobi_core", "doctor"],
        "registry": ["python3", "-m", "kirobi_core", "registry"],
        "keycodi": ["python3", "-m", "kirobi_core", "keycodi", payload.get("mission", "status")],
        "autonomous-once": ["python3", "-m", "kirobi_core", "autonomous-once"],
    }

    cmd = cmd_map.get(task_type)
    if not cmd:
        return {"success": False, "error": f"Unbekannter kirobi_core Task-Typ: {task_type}"}

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(REPO_ROOT),
        )
        output = proc.stdout.strip()
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            data = output

        return {
            "success": proc.returncode == 0,
            "output": data,
            "stderr": proc.stderr.strip() if proc.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout nach 60s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Agent-Router ─────────────────────────────────────────────────────────────

def dispatch(agent_name: str, task_type: str, payload: dict, zone: str = "WORKSPACE") -> dict:
    """Zentraler Dispatcher: leitet an den richtigen Agenten weiter."""

    # HTTP-Services direkt ansprechen
    if agent_name in HTTP_AGENTS:
        return call_http_agent(agent_name, task_type, payload)

    # kirobi_core CLI
    if agent_name == "kirobi-core":
        return call_kirobi_core(task_type, payload)

    # Python-Agenten (direkt importiert)
    if agent_name in ("hermes-reasoner", "hermes", "obsidian", "openclaw", "opencode"):
        return call_python_agent(agent_name, task_type, payload, zone)

    # Unbekannt → Liste der verfügbaren Agenten ausgeben
    return {
        "success": False,
        "error": f"Unbekannter Agent: '{agent_name}'",
        "available_agents": sorted(list(HTTP_AGENTS.keys()) + [
            "hermes-reasoner", "obsidian", "openclaw", "opencode", "kirobi-core"
        ]),
    }


# ─── Agenten-Inventar anzeigen ────────────────────────────────────────────────

def list_agents() -> dict:
    """Zeigt alle verfügbaren Agenten und ihre Fähigkeiten."""
    return {
        "python_agents": {
            "hermes-reasoner": {
                "task_types": ["chain_of_thought", "debate", "hypothesis", "research_synthesis", "classify_document"],
                "description": "Multi-Step-Reasoning, Dokument-Klassifizierung, Hypothesen",
                "zones": ["PUBLIC", "WORKSPACE"],
            },
            "obsidian": {
                "task_types": ["vault_read", "vault_write", "vault_list", "vault_query_links", "daily_note", "moc"],
                "description": "Obsidian-Vault CRUD, Knowledge-Graph, Daily Notes",
                "zones": ["PUBLIC", "WORKSPACE", "FAMILY_PRIVATE"],
            },
            "openclaw": {
                "task_types": ["web_fetch", "api_call_external", "filesystem_read", "browser_automation"],
                "description": "Web-Fetch, API-Calls, Browser-Automation",
                "zones": ["PUBLIC", "WORKSPACE", "QUARANTINE"],
            },
            "opencode": {
                "task_types": ["generate_code", "debug_code", "refactor_code", "code_review"],
                "description": "Code generieren, debuggen, reviewen",
                "zones": ["PUBLIC", "WORKSPACE"],
            },
        },
        "cli_agents": {
            "kirobi-core": {
                "task_types": ["status", "backlog", "scan", "doctor", "registry", "keycodi", "autonomous-once"],
                "description": "System-Status, Backlog, Diagnose, Orchestrierung",
            },
        },
        "http_agents": {
            name: {"base_url": url, "description": "HTTP-Service"}
            for name, url in HTTP_AGENTS.items()
        },
    }


# ─── Haupt-Entry-Point ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenDisruption Agent-Dispatcher — ruft registrierte Agenten auf"
    )
    parser.add_argument("--agent", "-a", help="Agent-Name")
    parser.add_argument("--task", "-t", default="status", help="Task-Typ")
    parser.add_argument("--payload", "-p", default="{}", help="JSON-Payload")
    parser.add_argument("--zone", "-z", default="WORKSPACE", help="Zone (default: WORKSPACE)")
    parser.add_argument("--list", action="store_true", help="Alle Agenten auflisten")
    parser.add_argument("--pretty", action="store_true", help="Pretty-Print JSON-Ausgabe")

    args = parser.parse_args()

    if args.list or not args.agent:
        result = list_agents()
    else:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            print(json.dumps({"success": False, "error": f"Ungültiger JSON-Payload: {e}"}))
            sys.exit(1)

        result = dispatch(args.agent, args.task, payload, args.zone)

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))

    if isinstance(result, dict) and result.get("success") is False:
        sys.exit(1)


if __name__ == "__main__":
    main()
