#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final, TypedDict
from urllib.parse import unquote

REPO_ROOT: Final = Path(__file__).resolve().parents[1]
CONFIG_PATH: Final = REPO_ROOT / "products" / "luki" / "config" / "luki.json"
WEB_ROOT: Final = REPO_ROOT / "products" / "luki" / "web"
DEFAULT_HOST: Final = "127.0.0.1"
DEFAULT_PORT: Final = 8411


class AskRequest(TypedDict):
    question: str


class AskResponse(TypedDict):
    answer: str
    sources: list[str]
    audit_id: str


class StatusResponse(TypedDict):
    ready: bool
    collection: str
    allow_cloud: bool
    audit_enabled: bool
    source_manifest_present: bool
    secrets_configured: bool


class GraphifyResponse(TypedDict):
    ready: bool
    nodes: int
    edges: int
    communities: int
    report_present: bool


@dataclass(frozen=True, slots=True)
class LukiConfig:
    collection: str
    allowed_collections: tuple[str, ...]
    allow_cloud: bool
    audit_enabled: bool
    data_root: Path
    secrets_file: Path


class RuntimeBoundaryError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        msg = f"{path} must contain a JSON object"
        raise TypeError(msg)
    return payload


def load_config(path: Path = CONFIG_PATH) -> LukiConfig:
    payload = _read_json(path)
    policy = payload.get("policy")
    audit = payload.get("audit")
    runtime = payload.get("runtime")
    if not isinstance(policy, dict) or not isinstance(audit, dict) or not isinstance(runtime, dict):
        msg = "luki.json requires policy, audit, and runtime objects"
        raise TypeError(msg)
    collection = payload.get("collection")
    allowed_collections = policy.get("allowed_collections")
    allow_cloud = policy.get("allow_cloud")
    audit_enabled = audit.get("enabled")
    data_root = runtime.get("data_root")
    secrets_file = runtime.get("secrets_file")
    if not isinstance(collection, str):
        msg = "collection must be a string"
        raise TypeError(msg)
    if not isinstance(allowed_collections, list) or not all(
        isinstance(item, str) for item in allowed_collections
    ):
        msg = "policy.allowed_collections must be a list of strings"
        raise TypeError(msg)
    allowed = tuple(allowed_collections)
    if collection not in allowed:
        msg = f"collection {collection!r} is not in the LUKI allowlist"
        raise RuntimeBoundaryError(msg)
    if not isinstance(allow_cloud, bool) or not isinstance(audit_enabled, bool):
        msg = "allow_cloud and audit.enabled must be booleans"
        raise TypeError(msg)
    if not isinstance(data_root, str) or not isinstance(secrets_file, str):
        msg = "runtime.data_root and runtime.secrets_file must be strings"
        raise TypeError(msg)
    return LukiConfig(
        collection=collection,
        allowed_collections=allowed,
        allow_cloud=allow_cloud,
        audit_enabled=audit_enabled,
        data_root=Path(data_root),
        secrets_file=Path(secrets_file),
    )


def status_payload(config: LukiConfig) -> StatusResponse:
    manifest = REPO_ROOT / "products" / "luki" / "source-docs" / "manifest.json"
    return {
        "ready": manifest.exists() and not config.allow_cloud,
        "collection": config.collection,
        "allow_cloud": config.allow_cloud,
        "audit_enabled": config.audit_enabled,
        "source_manifest_present": manifest.exists(),
        "secrets_configured": config.secrets_file.exists(),
    }


def graphify_payload(root: Path = REPO_ROOT) -> GraphifyResponse:
    graph_path = root / "graphify-out" / "graph.json"
    report_path = root / "graphify-out" / "GRAPH_REPORT.md"
    if not graph_path.exists():
        return {"ready": False, "nodes": 0, "edges": 0, "communities": 0, "report_present": False}
    payload = _read_json(graph_path)
    nodes = payload.get("nodes")
    links = payload.get("links")
    communities = {
        node.get("community")
        for node in nodes
        if isinstance(node, dict) and node.get("community") is not None
    } if isinstance(nodes, list) else set()
    return {
        "ready": True,
        "nodes": len(nodes) if isinstance(nodes, list) else 0,
        "edges": len(links) if isinstance(links, list) else 0,
        "communities": len(communities),
        "report_present": report_path.exists(),
    }


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _audit_path(config: LukiConfig, now: datetime) -> Path:
    data_root = config.data_root.resolve()
    repo_root = REPO_ROOT.resolve()
    if data_root == repo_root or repo_root in data_root.parents:
        msg = f"runtime data root must be outside the repository: {data_root}"
        raise RuntimeBoundaryError(msg)
    return data_root / "luki" / "audit" / now.strftime("%Y-%m") / f"luki-audit-{now:%Y-%m-%d}.jsonl"


def answer_question(request: AskRequest, config: LukiConfig, now: datetime | None = None) -> AskResponse:
    question = request["question"].strip()
    if len(question) == 0:
        audit_id = _sha256("empty-question")[:16]
        return {"answer": "Bitte eine Frage eingeben.", "sources": [], "audit_id": audit_id}
    current_time = now if now is not None else datetime.now(UTC)
    answer = "Ich weiß es nicht. Der Retrieval-Index ist im MVP-Skelett noch nicht belegt."
    audit_id = _sha256(f"{current_time.isoformat()}:{question}")[:16]
    if config.audit_enabled:
        audit_file = _audit_path(config, current_time)
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "time": current_time.isoformat(),
            "audit_id": audit_id,
            "user_hash": _sha256("local-mvp-user"),
            "question_hash": _sha256(question),
            "answer_hash": _sha256(answer),
            "collection": config.collection,
            "source_ids": [],
            "model": "not-run",
        }
        with audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        audit_file.chmod(0o600)
    return {"answer": answer, "sources": [], "audit_id": audit_id}


class LukiHandler(BaseHTTPRequestHandler):
    server_version = "OpenDisruptionLukiMVP/0.1"

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file() or WEB_ROOT not in path.resolve().parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = "text/html; charset=utf-8"
        if path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        if path.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        config = load_config()
        if self.path == "/api/health":
            self._send_json({"ok": True})
            return
        if self.path == "/api/status":
            self._send_json(status_payload(config))
            return
        if self.path == "/api/graphify":
            self._send_json(graphify_payload())
            return
        relative = "index.html" if self.path == "/" else unquote(self.path.lstrip("/"))
        self._send_file((WEB_ROOT / relative).resolve())

    def do_POST(self) -> None:
        if self.path != "/api/ask":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(payload, dict) or not isinstance(payload.get("question"), str):
            self._send_json({"error": "question must be a string"}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(answer_question({"question": payload["question"]}, load_config()))

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="luki_mvp_server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), LukiHandler)
    print(f"LUKI MVP UI: http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
