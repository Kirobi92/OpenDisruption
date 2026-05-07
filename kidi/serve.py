"""
kidi/serve.py
Zone: WORKSPACE

MCP-kompatibler Server für den KeyCodi Context-DB.
Kommuniziert über stdio mit JSON-RPC 2.0 (newline-delimited JSON).

Unterstützte Tools:
    - context_store:  Speichert Kontext-Information (nur PUBLIC/WORKSPACE)
    - context_get:    Liest Kontext-Information
    - context_list:   Listet alle Keys
    - context_delete: Löscht einen Key
    - backlog_query:  Fragt den kirobi_core Backlog ab
    - zone_classify:  Klassifiziert einen Pfad nach Zone
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

from kirobi_core.zones import classify

from .context_db.store import (
    delete_context,
    get_context,
    list_context,
    store_context,
)

# MCP-Protokollversion
_PROTOCOL_VERSION = "2024-11-05"
_SERVER_NAME = "kirobi-context-db"
_SERVER_VERSION = "1.0.0"

# Tool-Definitionen für tools/list
_TOOLS: list[dict] = [
    {
        "name": "context_store",
        "description": "Speichert Kontext-Information in der lokalen SQLite-DB (nur PUBLIC/WORKSPACE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Eindeutiger Schlüssel"},
                "value": {"type": "string", "description": "Zu speichernder Wert"},
                "zone": {
                    "type": "string",
                    "enum": ["PUBLIC", "WORKSPACE"],
                    "description": "Zone des Eintrags",
                },
                "ttl_seconds": {
                    "type": "integer",
                    "description": "Optionale Lebensdauer in Sekunden",
                },
            },
            "required": ["key", "value", "zone"],
        },
    },
    {
        "name": "context_get",
        "description": "Liest einen Kontext-Eintrag anhand des Schlüssels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Schlüssel des Eintrags"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "context_list",
        "description": "Listet alle Kontext-Keys, optional gefiltert nach Zone oder Präfix.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "zone": {
                    "type": "string",
                    "description": "Optionaler Zone-Filter",
                },
                "prefix": {
                    "type": "string",
                    "description": "Optionaler Key-Präfix-Filter",
                },
            },
        },
    },
    {
        "name": "context_delete",
        "description": "Löscht einen Kontext-Eintrag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Schlüssel des zu löschenden Eintrags"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "backlog_query",
        "description": "Fragt den kirobi_core Backlog ab und gibt priorisierte Tasks zurück.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximale Anzahl Tasks (default: 10)",
                    "default": 10,
                },
                "priority": {
                    "type": "string",
                    "description": "Optionaler Prioritäts-Filter (z.B. 'high', 'medium', 'low')",
                },
            },
        },
    },
    {
        "name": "zone_classify",
        "description": "Klassifiziert einen Dateipfad nach dem OpenDisruption Zonen-Modell.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Zu klassifizierender Pfad"},
            },
            "required": ["path"],
        },
    },
]


def _make_response(request_id: Any, result: Any) -> dict:
    """Erstellt eine JSON-RPC 2.0 Erfolgs-Antwort."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _make_error(request_id: Any, code: int, message: str) -> dict:
    """Erstellt eine JSON-RPC 2.0 Fehler-Antwort."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _handle_initialize(params: dict) -> dict:
    """Verarbeitet die MCP initialize-Anfrage."""
    return {
        "protocolVersion": _PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": _SERVER_NAME, "version": _SERVER_VERSION},
    }


def _handle_tools_list(params: dict) -> dict:
    """Gibt die Liste aller verfügbaren Tools zurück."""
    return {"tools": _TOOLS}


def _handle_tool_context_store(args: dict) -> dict:
    """Führt das context_store Tool aus."""
    key = args["key"]
    value = args["value"]
    zone = args["zone"]
    ttl_seconds: Optional[int] = args.get("ttl_seconds")

    result = store_context(key, value, zone, ttl_seconds)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"stored": True, **result}),
            }
        ]
    }


def _handle_tool_context_get(args: dict) -> dict:
    """Führt das context_get Tool aus."""
    key = args["key"]
    entry = get_context(key)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(entry),
            }
        ]
    }


def _handle_tool_context_list(args: dict) -> dict:
    """Führt das context_list Tool aus."""
    zone: Optional[str] = args.get("zone")
    prefix: Optional[str] = args.get("prefix")
    entries = list_context(zone=zone, prefix=prefix)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(entries),
            }
        ]
    }


def _handle_tool_context_delete(args: dict) -> dict:
    """Führt das context_delete Tool aus."""
    key = args["key"]
    deleted = delete_context(key)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"deleted": deleted}),
            }
        ]
    }


def _handle_tool_backlog_query(args: dict) -> dict:
    """Führt das backlog_query Tool aus."""
    from kirobi_core.backlog import generate_backlog
    from kirobi_core.scanner import scan_repository

    limit: int = args.get("limit", 10)
    priority_filter: Optional[str] = args.get("priority")

    # Repo-Root ermitteln: Elternverzeichnis von kidi/
    repo_root = Path(__file__).parent.parent
    scan = scan_repository(repo_root)
    tasks = generate_backlog(scan)

    # Optionaler Prioritäts-Filter
    if priority_filter:
        tasks = [t for t in tasks if t.priority.lower() == priority_filter.lower()]

    tasks = tasks[:limit]
    task_dicts = [t.to_dict() for t in tasks]

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(task_dicts),
            }
        ]
    }


def _handle_tool_zone_classify(args: dict) -> dict:
    """Führt das zone_classify Tool aus."""
    path = args["path"]
    zone = classify(path)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"path": path, "zone": str(zone.name)}),
            }
        ]
    }


# Dispatch-Tabelle für Tool-Handler
_TOOL_HANDLERS = {
    "context_store": _handle_tool_context_store,
    "context_get": _handle_tool_context_get,
    "context_list": _handle_tool_context_list,
    "context_delete": _handle_tool_context_delete,
    "backlog_query": _handle_tool_backlog_query,
    "zone_classify": _handle_tool_zone_classify,
}


def _handle_tools_call(params: dict) -> dict:
    """Dispatcht einen tools/call-Request an den passenden Handler."""
    tool_name: str = params.get("name", "")
    arguments: dict = params.get("arguments", {})

    handler = _TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unbekanntes Tool: '{tool_name}'")

    return handler(arguments)


# Dispatch-Tabelle für Methoden
_METHOD_HANDLERS = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
}


def _process_request(raw_line: str) -> Optional[dict]:
    """
    Verarbeitet eine einzelne JSON-RPC Anfrage.

    Args:
        raw_line: Rohe JSON-Zeile vom stdin

    Returns:
        Response-Dict oder None bei Notifications (kein id)
    """
    try:
        request = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        return _make_error(None, -32700, f"Parse error: {exc}")

    request_id = request.get("id")
    method: str = request.get("method", "")
    params: dict = request.get("params") or {}

    # Notification (kein id) → keine Antwort nötig
    if "id" not in request:
        return None

    handler = _METHOD_HANDLERS.get(method)
    if handler is None:
        return _make_error(request_id, -32601, f"Method not found: '{method}'")

    try:
        result = handler(params)
        return _make_response(request_id, result)
    except (ValueError, KeyError) as exc:
        return _make_error(request_id, -32602, f"Invalid params: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"[kidi/serve] Fehler bei '{method}': {exc}", file=sys.stderr)
        return _make_error(request_id, -32603, f"Internal error: {exc}")


def run_server(port: Optional[int] = None) -> None:
    """
    Startet den MCP-Server im stdio-Modus.

    Der port-Parameter wird ignoriert (stdio-only), ist aber für CLI-Kompatibilität vorhanden.

    Args:
        port: Wird ignoriert (stdio-Transport)
    """
    print(
        f"[kidi/serve] {_SERVER_NAME} v{_SERVER_VERSION} gestartet (stdio-Transport)",
        file=sys.stderr,
    )

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        response = _process_request(raw_line)
        if response is not None:
            print(json.dumps(response), flush=True)
