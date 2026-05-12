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
        telegram_url=f"http://127.0.0.1:{port}",
        embeddings_url=f"http://127.0.0.1:{port}",
        retrieval_url=f"http://127.0.0.1:{port}",
        ingest_url=f"http://127.0.0.1:{port}",
        model_routing_url=f"http://127.0.0.1:{port}",
        analytics_url=f"http://127.0.0.1:{port}",
        image_generation_url=f"http://127.0.0.1:{port}",
        media_processing_url=f"http://127.0.0.1:{port}",
        music_generation_url=f"http://127.0.0.1:{port}",
        video_generation_url=f"http://127.0.0.1:{port}",
        web_url=f"http://127.0.0.1:{port}",
        dashboard_url=f"http://127.0.0.1:{port}",
        voice_app_url=f"http://127.0.0.1:{port}",
        caddy_url=f"http://127.0.0.1:{port}",
    )
    statuses = services.probe_all(closed_cfg, timeout=0.3)
    names = [s.name for s in statuses]
    assert names == [
        "ollama",
        "open-webui",
        "qdrant",
        "postgres",
        "flowise",
        "voice",
        "auth",
        "api",
        "telegram",
        "embeddings",
        "ingest",
        "retrieval",
        "model-routing",
        "analytics",
        "image-generation",
        "media-processing",
        "music-generation",
        "video-generation",
        "web",
        "dashboard",
        "voice-app",
        "caddy",
    ]
    assert all(not s.ok for s in statuses)


def test_stack_config_from_env_covers_active_compose_ports():
    cfg = services.StackConfig.from_env({"KIROBI_HOST": "127.0.0.1"})
    ports_by_name = {
        "ollama": "11434",
        "open-webui": "3000",
        "qdrant": "6333",
        "postgres": "5432",
        "flowise": "3001",
        "voice": "8001",
        "auth": "8002",
        "api": "8003",
        "telegram": "8005",
        "embeddings": "8004",
        "ingest": "8007",
        "retrieval": "8006",
        "model-routing": "8009",
        "analytics": "8010",
        "image-generation": "8011",
        "media-processing": "8012",
        "music-generation": "8013",
        "video-generation": "8014",
        "web": "3002",
        "dashboard": "3003",
        "voice-app": "3004",
        "caddy": "80",
    }
    urls_by_name = {
        "ollama": cfg.ollama_url,
        "open-webui": cfg.openwebui_url,
        "qdrant": cfg.qdrant_url,
        "postgres": f"tcp://{cfg.postgres_host}:{cfg.postgres_port}",
        "flowise": cfg.flowise_url,
        "voice": cfg.voice_url,
        "auth": cfg.auth_url,
        "api": cfg.api_url,
        "telegram": cfg.telegram_url,
        "embeddings": cfg.embeddings_url,
        "ingest": cfg.ingest_url,
        "retrieval": cfg.retrieval_url,
        "model-routing": cfg.model_routing_url,
        "analytics": cfg.analytics_url,
        "image-generation": cfg.image_generation_url,
        "media-processing": cfg.media_processing_url,
        "music-generation": cfg.music_generation_url,
        "video-generation": cfg.video_generation_url,
        "web": cfg.web_url,
        "dashboard": cfg.dashboard_url,
        "voice-app": cfg.voice_app_url,
        "caddy": cfg.caddy_url,
    }
    assert urls_by_name.keys() == ports_by_name.keys()
    for name, port in ports_by_name.items():
        assert urls_by_name[name].endswith(f":{port}")


def test_new_python_entrypoints_compile():
    import py_compile

    for path in (
        REPO_ROOT / "infra" / "scripts" / "init-qdrant.py",
        REPO_ROOT / "services" / "telegram" / "main.py",
        REPO_ROOT / "kirobi_core" / "keycodi.py",
        REPO_ROOT / "kirobi_core" / "services.py",
        REPO_ROOT / "kirobi_core" / "qdrant_collections.py",
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
    assert "Alle 14 Collections verarbeitet" in result.stdout
    assert "kirobi_workspace" in result.stdout
    assert "kirobi_workspace_document" not in result.stdout


def test_telegram_service_escapes_html_replies():
    src = (REPO_ROOT / "services" / "telegram" / "main.py").read_text()
    assert "from html import escape" in src
    assert "def _html" in src
    assert "_html(" in src
