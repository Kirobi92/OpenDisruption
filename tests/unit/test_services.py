"""Tests for kirobi_core.services — stdlib HTTP probes."""
from __future__ import annotations

import contextlib
import http.server
import json
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from kirobi_core import services


REPO_ROOT = Path(__file__).resolve().parents[2]


class _Handler(http.server.BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, Any]] = {}

    def log_message(self, *args, **kwargs):  # silence test noise
        return

    def do_GET(self):  # noqa: N802
        status, body = self.routes.get(self.path, (404, {"error": "not found"}))
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))


@contextlib.contextmanager
def _server(routes: dict[str, tuple[int, Any]]):
    handler_cls = type("H", (_Handler,), {"routes": routes})
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_probe_ollama_success():
    routes = {"/api/tags": (200, {"models": [{"name": "llama3.1:8b"}, {"name": "bge-m3"}]})}
    with _server(routes) as base:
        s = services.probe_ollama(base, timeout=3)
    assert s.ok is True
    assert s.name == "ollama"
    assert "llama3.1:8b" in s.extra["models"]


def test_probe_qdrant_success():
    routes = {"/collections": (200, {"result": {"collections": [{"name": "kirobi_workspace"}]}})}
    with _server(routes) as base:
        s = services.probe_qdrant(base, timeout=3)
    assert s.ok is True
    assert "kirobi_workspace" in s.extra["collections"]


def test_probe_health_endpoint():
    routes = {"/health": (200, {"status": "ok"})}
    with _server(routes) as base:
        s = services.probe_health_endpoint("api", base, timeout=3)
    assert s.ok is True


def test_probe_offline_service_is_soft_failure():
    # Pick an unused port — connect should fail fast.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    s = services.probe_http("ghost", f"http://127.0.0.1:{port}/", timeout=0.3)
    assert s.ok is False
    assert "Error" in s.detail or "refus" in s.detail.lower() or "timed out" in s.detail.lower()


def test_probe_postgres_tcp_reachable():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    try:
        s = services.probe_postgres("127.0.0.1", port, timeout=1.0)
        assert s.ok is True
        assert "TCP" in s.detail
    finally:
        sock.close()


def test_probe_postgres_unreachable():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    s = services.probe_postgres("127.0.0.1", port, timeout=0.3)
    assert s.ok is False


def test_stack_config_from_env_uses_kirobi_host():
    cfg = services.StackConfig.from_env({"KIROBI_HOST": "10.0.0.1"})
    assert "10.0.0.1" in cfg.ollama_url
    assert cfg.postgres_host == "10.0.0.1"


def test_render_table_contains_all_services():
    cfg = services.StackConfig.from_env({"KIROBI_HOST": "127.0.0.1"})
    statuses = [
        services.ServiceStatus("ollama", cfg.ollama_url, ok=False, detail="x"),
        services.ServiceStatus("qdrant", cfg.qdrant_url, ok=True, detail="y"),
    ]
    txt = services.render_table(statuses)
    assert "ollama" in txt and "qdrant" in txt
    assert "1/2" in txt


def test_probe_all_returns_one_per_service(monkeypatch):
    cfg = services.StackConfig.from_env({"KIROBI_HOST": "127.0.0.1"})
    # Force failures by using an unused port.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    closed_cfg = services.StackConfig(
        ollama_url=f"http://127.0.0.1:{port}",
        qdrant_url=f"http://127.0.0.1:{port}",
        postgres_host="127.0.0.1",
        postgres_port=port,
        voice_url=f"http://127.0.0.1:{port}",
        auth_url=f"http://127.0.0.1:{port}",
        api_url=f"http://127.0.0.1:{port}",
        openwebui_url=f"http://127.0.0.1:{port}",
        flowise_url=f"http://127.0.0.1:{port}",
    )
    statuses = services.probe_all(closed_cfg, timeout=0.3)
    names = [s.name for s in statuses]
    assert names == ["ollama", "qdrant", "postgres", "voice", "auth", "api", "open-webui", "flowise"]
    assert all(not s.ok for s in statuses)


def test_new_python_entrypoints_compile():
    import py_compile

    for path in (
        REPO_ROOT / "infra" / "scripts" / "init-qdrant.py",
        REPO_ROOT / "services" / "telegram" / "main.py",
        REPO_ROOT / "kirobi_core" / "keycodi.py",
    ):
        py_compile.compile(str(path), doraise=True)


def test_qdrant_init_dry_run_without_live_qdrant():
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "infra" / "scripts" / "init-qdrant.py"),
            "--dry-run",
            "--qdrant-url",
            "http://127.0.0.1:9",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
    assert "DRY-RUN" in result.stdout
    assert "Alle 7 Collections verarbeitet" in result.stdout


def test_telegram_service_escapes_html_replies():
    src = (REPO_ROOT / "services" / "telegram" / "main.py").read_text()
    assert "from html import escape" in src
    assert "def _html" in src
    assert "_html(ai_response)" in src
