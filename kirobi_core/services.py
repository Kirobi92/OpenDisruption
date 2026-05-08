"""Stdlib-only probes & clients for the Kirobi service stack.

Speaks directly with the running services defined in
``docker-compose.yml`` and ``AGENTS.md``. All probes are **timeout-bounded**, **read-only**
and **fail soft** — when a service is unreachable they return a
:class:`ServiceStatus` with ``ok=False`` instead of raising.

The implementation deliberately avoids ``httpx`` / ``requests`` / 
``asyncpg`` so the package keeps its zero-dependency promise. It uses
:mod:`urllib.request` for HTTP probes and :mod:`socket` for the
TCP-level Postgres reachability check.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable

DEFAULT_TIMEOUT = 2.0


# --------------------------------------------------------------------- types
@dataclass
class ServiceStatus:
    """Result of one service probe."""

    name: str
    url: str
    ok: bool
    detail: str = ""
    latency_ms: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "ok": self.ok,
            "detail": self.detail,
            "latency_ms": self.latency_ms,
            "extra": dict(self.extra),
        }


# ---------------------------------------------------------------- helpers
def _http_get_json(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> tuple[int, Any]:
    """GET *url* and return ``(status_code, parsed_json_or_text)``.

    Accepts both 200 and other 2xx/3xx responses. Raises
    :class:`urllib.error.URLError` (or subclasses) on transport failure.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "kirobi-core/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — fixed scheme
        raw = resp.read()
        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct or raw[:1] in (b"{", b"["):
            try:
                return resp.status, json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return resp.status, raw.decode("utf-8", errors="replace")
        return resp.status, raw.decode("utf-8", errors="replace")


def _measure(callable_, *args, **kwargs) -> tuple[int, Any | Exception]:
    """Run *callable_* and return ``(latency_ms, result_or_exception)``."""
    import time

    start = time.monotonic()
    try:
        result = callable_(*args, **kwargs)
        return int((time.monotonic() - start) * 1000), result
    except Exception as exc:  # noqa: BLE001 — soft probe
        return int((time.monotonic() - start) * 1000), exc


# -------------------------------------------------------------- env-config
@dataclass(frozen=True)
class StackConfig:
    """Service URLs / hosts derived from environment (compose defaults)."""

    ollama_url: str
    qdrant_url: str
    postgres_host: str
    postgres_port: int
    voice_url: str
    auth_url: str
    api_url: str
    openwebui_url: str
    flowise_url: str
    telegram_url: str
    embeddings_url: str
    retrieval_url: str
    ingest_url: str
    model_routing_url: str
    analytics_url: str
    image_generation_url: str
    media_processing_url: str
    music_generation_url: str
    video_generation_url: str
    web_url: str
    dashboard_url: str
    voice_app_url: str
    caddy_url: str

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "StackConfig":
        e = env if env is not None else os.environ
        host = e.get("KIROBI_HOST", "127.0.0.1")
        return cls(
            ollama_url=e.get("OLLAMA_BASE_URL", f"http://{host}:{e.get('OLLAMA_PORT', '11434')}"),
            qdrant_url=e.get("QDRANT_URL", f"http://{host}:{e.get('QDRANT_PORT', '6333')}"),
            postgres_host=e.get("POSTGRES_HOST", host),
            postgres_port=int(e.get("POSTGRES_PORT", "5432")),
            voice_url=e.get("VOICE_SERVICE_URL", f"http://{host}:{e.get('VOICE_PORT', '8001')}"),
            auth_url=e.get("AUTH_SERVICE_URL", f"http://{host}:{e.get('AUTH_PORT', '8002')}"),
            api_url=e.get("API_SERVICE_URL", f"http://{host}:{e.get('API_PORT', '8003')}"),
            openwebui_url=e.get("OPENWEBUI_URL", f"http://{host}:{e.get('OPENWEBUI_PORT', '3000')}"),
            flowise_url=e.get("FLOWISE_URL", f"http://{host}:{e.get('FLOWISE_PORT', '3001')}"),
            telegram_url=e.get("TELEGRAM_SERVICE_URL", f"http://{host}:{e.get('TELEGRAM_SERVICE_PORT', '8005')}"),
            embeddings_url=e.get("EMBEDDINGS_SERVICE_URL", f"http://{host}:{e.get('EMBEDDINGS_PORT', '8004')}"),
            retrieval_url=e.get("RETRIEVAL_SERVICE_URL", f"http://{host}:{e.get('RETRIEVAL_PORT', '8006')}"),
            ingest_url=e.get("INGEST_SERVICE_URL", f"http://{host}:{e.get('INGEST_PORT', '8007')}"),
            model_routing_url=e.get("MODEL_ROUTING_SERVICE_URL", f"http://{host}:{e.get('MODEL_ROUTING_PORT', '8009')}"),
            analytics_url=e.get("ANALYTICS_SERVICE_URL", f"http://{host}:{e.get('ANALYTICS_PORT', '8010')}"),
            image_generation_url=e.get("IMAGE_GENERATION_SERVICE_URL", f"http://{host}:{e.get('IMAGE_GENERATION_PORT', '8011')}"),
            media_processing_url=e.get("MEDIA_PROCESSING_SERVICE_URL", f"http://{host}:{e.get('MEDIA_PROCESSING_PORT', '8012')}"),
            music_generation_url=e.get("MUSIC_GENERATION_SERVICE_URL", f"http://{host}:{e.get('MUSIC_GENERATION_PORT', '8013')}"),
            video_generation_url=e.get("VIDEO_GENERATION_SERVICE_URL", f"http://{host}:{e.get('VIDEO_GENERATION_PORT', '8014')}"),
            web_url=e.get("WEB_URL", f"http://{host}:{e.get('WEB_PORT', '3002')}"),
            dashboard_url=e.get("DASHBOARD_URL", f"http://{host}:{e.get('DASHBOARD_PORT', '3003')}"),
            voice_app_url=e.get("VOICE_APP_URL", f"http://{host}:{e.get('VOICE_APP_PORT', '3004')}"),
            caddy_url=e.get("CADDY_URL", f"http://{host}:{e.get('CADDY_HTTP_PORT', '80')}"),
        )


# --------------------------------------------------------------- probes
def probe_http(name: str, url: str, *, timeout: float = DEFAULT_TIMEOUT) -> ServiceStatus:
    """Generic HTTP probe — accepts any 2xx/3xx as success."""
    latency, result = _measure(_http_get_json, url, timeout=timeout)
    if isinstance(result, Exception):
        return ServiceStatus(name=name, url=url, ok=False,
                             detail=f"{type(result).__name__}: {result}",
                             latency_ms=latency)
    status, body = result
    ok = 200 <= status < 400
    detail = f"HTTP {status}"
    extra: dict[str, Any] = {}
    if isinstance(body, dict):
        extra["body_keys"] = sorted(body.keys())[:8]
    return ServiceStatus(name=name, url=url, ok=ok, detail=detail,
                         latency_ms=latency, extra=extra)


def probe_ollama(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> ServiceStatus:
    """Probe Ollama via ``/api/tags`` (lists installed models)."""
    endpoint = url.rstrip("/") + "/api/tags"
    latency, result = _measure(_http_get_json, endpoint, timeout=timeout)
    if isinstance(result, Exception):
        return ServiceStatus(name="ollama", url=endpoint, ok=False,
                             detail=f"{type(result).__name__}: {result}",
                             latency_ms=latency)
    status, body = result
    if not (200 <= status < 400):
        return ServiceStatus(name="ollama", url=endpoint, ok=False,
                             detail=f"HTTP {status}", latency_ms=latency)
    models: list[str] = []
    if isinstance(body, dict) and isinstance(body.get("models"), list):
        for m in body["models"]:
            if isinstance(m, dict) and isinstance(m.get("name"), str):
                models.append(m["name"])
    return ServiceStatus(
        name="ollama", url=endpoint, ok=True,
        detail=f"{len(models)} model(s)", latency_ms=latency,
        extra={"models": models[:10]},
    )


def probe_qdrant(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> ServiceStatus:
    """Probe Qdrant via ``/collections``."""
    endpoint = url.rstrip("/") + "/collections"
    latency, result = _measure(_http_get_json, endpoint, timeout=timeout)
    if isinstance(result, Exception):
        return ServiceStatus(name="qdrant", url=endpoint, ok=False,
                             detail=f"{type(result).__name__}: {result}",
                             latency_ms=latency)
    status, body = result
    if not (200 <= status < 400):
        return ServiceStatus(name="qdrant", url=endpoint, ok=False,
                             detail=f"HTTP {status}", latency_ms=latency)
    collections: list[str] = []
    if isinstance(body, dict):
        result_obj = body.get("result", {})
        if isinstance(result_obj, dict):
            for c in result_obj.get("collections", []) or []:
                if isinstance(c, dict) and isinstance(c.get("name"), str):
                    collections.append(c["name"])
    return ServiceStatus(
        name="qdrant", url=endpoint, ok=True,
        detail=f"{len(collections)} collection(s)", latency_ms=latency,
        extra={"collections": collections[:16]},
    )


def probe_postgres(host: str, port: int, *, timeout: float = DEFAULT_TIMEOUT) -> ServiceStatus:
    """TCP-level reachability check for Postgres (no auth needed)."""
    url = f"tcp://{host}:{port}"
    latency, result = _measure(_tcp_connect, host, port, timeout)
    if isinstance(result, Exception):
        return ServiceStatus(name="postgres", url=url, ok=False,
                             detail=f"{type(result).__name__}: {result}",
                             latency_ms=latency)
    return ServiceStatus(name="postgres", url=url, ok=True,
                         detail="TCP reachable", latency_ms=latency)


def _tcp_connect(host: str, port: int, timeout: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True
    finally:
        sock.close()


def probe_health_endpoint(name: str, url: str, *, timeout: float = DEFAULT_TIMEOUT) -> ServiceStatus:
    """Probe a FastAPI service's ``/health`` endpoint."""
    endpoint = url.rstrip("/") + "/health"
    return probe_http(name, endpoint, timeout=timeout)


# ----------------------------------------------------------- aggregation
def probe_all(config: StackConfig | None = None,
              *, timeout: float = DEFAULT_TIMEOUT) -> list[ServiceStatus]:
    """Probe every HTTP/port-probbable active Compose service from AGENTS.md.

    ``supervisor`` has no host port in the active compose stack, so it is not
    probed here. ``caddy`` is included via its HTTP entrypoint; HTTPS is skipped
    because local certificates are deployment-specific.
    """
    cfg = config or StackConfig.from_env()
    return [
        probe_ollama(cfg.ollama_url, timeout=timeout),
        probe_http("open-webui", cfg.openwebui_url, timeout=timeout),
        probe_qdrant(cfg.qdrant_url, timeout=timeout),
        probe_postgres(cfg.postgres_host, cfg.postgres_port, timeout=timeout),
        probe_http("flowise", cfg.flowise_url, timeout=timeout),
        probe_health_endpoint("voice", cfg.voice_url, timeout=timeout),
        probe_health_endpoint("auth", cfg.auth_url, timeout=timeout),
        probe_health_endpoint("api", cfg.api_url, timeout=timeout),
        probe_health_endpoint("telegram", cfg.telegram_url, timeout=timeout),
        probe_health_endpoint("embeddings", cfg.embeddings_url, timeout=timeout),
        probe_health_endpoint("ingest", cfg.ingest_url, timeout=timeout),
        probe_health_endpoint("retrieval", cfg.retrieval_url, timeout=timeout),
        probe_health_endpoint("model-routing", cfg.model_routing_url, timeout=timeout),
        probe_health_endpoint("analytics", cfg.analytics_url, timeout=timeout),
        probe_health_endpoint("image-generation", cfg.image_generation_url, timeout=timeout),
        probe_health_endpoint("media-processing", cfg.media_processing_url, timeout=timeout),
        probe_health_endpoint("music-generation", cfg.music_generation_url, timeout=timeout),
        probe_health_endpoint("video-generation", cfg.video_generation_url, timeout=timeout),
        probe_http("web", cfg.web_url, timeout=timeout),
        probe_http("dashboard", cfg.dashboard_url, timeout=timeout),
        probe_http("voice-app", cfg.voice_app_url, timeout=timeout),
        probe_http("caddy", cfg.caddy_url, timeout=timeout),
    ]


def render_table(statuses: Iterable[ServiceStatus]) -> str:
    """Return a compact, fixed-width status table for CLI output."""
    rows: list[ServiceStatus] = list(statuses)
    if not rows:
        return "(no services probed)"
    name_w = max(len(r.name) for r in rows)
    url_w = max(len(r.url) for r in rows)
    out = ["Kirobi Stack Status", "=" * 30]
    for r in rows:
        sym = "✓" if r.ok else "✗"
        out.append(
            f"  {sym} {r.name.ljust(name_w)}  "
            f"{r.url.ljust(url_w)}  "
            f"{r.latency_ms:>5}ms  {r.detail}"
        )
    ok = sum(1 for r in rows if r.ok)
    out.append(f"\nSummary: {ok}/{len(rows)} services reachable")
    return "\n".join(out)
