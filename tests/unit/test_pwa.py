"""PWA / reverse-proxy / first-run integration tests.

These tests are pure stdlib + pytest — they validate the *static*
configuration that drives the family PWA on `kirobi.local` so the
end-to-end flow is verified in CI without Docker.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC = REPO_ROOT / "apps" / "web" / "public"


# --- Manifest ---------------------------------------------------------------
def test_manifest_is_valid_json_with_required_fields():
    manifest = json.loads((PUBLIC / "manifest.json").read_text())
    for key in (
        "name",
        "short_name",
        "icons",
        "start_url",
        "display",
        "theme_color",
        "background_color",
        "scope",
    ):
        assert key in manifest, f"manifest is missing {key}"
    assert manifest["display"] in {"standalone", "fullscreen", "minimal-ui"}
    assert manifest["lang"] == "de"
    assert isinstance(manifest["icons"], list) and manifest["icons"]


def test_manifest_has_any_and_maskable_icons():
    icons = json.loads((PUBLIC / "manifest.json").read_text())["icons"]
    purposes = {i.get("purpose", "any") for i in icons if "png" in i["src"]}
    assert "any" in purposes, "PWA needs an `any`-purpose PNG icon"
    assert "maskable" in purposes, "PWA needs a `maskable`-purpose PNG icon"


def test_manifest_referenced_files_exist():
    icons = json.loads((PUBLIC / "manifest.json").read_text())["icons"]
    for icon in icons:
        path = PUBLIC / icon["src"].lstrip("/")
        assert path.is_file(), f"manifest references missing icon {path}"


def test_required_pwa_assets_exist():
    for name in (
        "manifest.json",
        "icon.svg",
        "icon-192.png",
        "icon-512.png",
        "icon-192-maskable.png",
        "icon-512-maskable.png",
        "apple-touch-icon.png",
        "favicon.ico",
        "offline.html",
        "robots.txt",
    ):
        assert (PUBLIC / name).is_file(), f"missing public asset: {name}"


def test_png_icons_have_expected_size():
    """Quick smoke: read the PNG IHDR chunk and confirm dimensions."""
    expectations = {
        "icon-192.png": (192, 192),
        "icon-512.png": (512, 512),
        "icon-192-maskable.png": (192, 192),
        "icon-512-maskable.png": (512, 512),
        "apple-touch-icon.png": (180, 180),
    }
    for name, (w, h) in expectations.items():
        data = (PUBLIC / name).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{name} is not a PNG"
        # IHDR width/height live at offset 16 (8 byte header + 4 length + 4 type).
        width, height = struct.unpack(">II", data[16:24])
        assert (width, height) == (w, h), f"{name} is {width}x{height}, expected {w}x{h}"


# --- Caddyfile --------------------------------------------------------------
def test_caddyfile_exposes_all_routes():
    cf = (REPO_ROOT / "infra" / "caddy" / "Caddyfile").read_text()
    # Routes the PWA needs.
    assert "reverse_proxy web:3000" in cf
    assert "reverse_proxy auth:8000" in cf
    assert "reverse_proxy api:8000" in cf
    assert "/api/auth/*" in cf
    assert "/api/*" in cf
    assert "/open-webui/*" in cf
    assert "/flowise/*" in cf
    assert "/qdrant/*" in cf
    assert "100.64.0.0/10" in cf
    # mDNS hostname is configurable.
    assert "{$KIROBI_HOSTNAME" in cf
    # TLS: internal CA so PWA install prompt works on LAN.
    assert "tls internal" in cf


def test_compose_includes_caddy_with_lan_binding():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "kirobi-caddy" in compose
    # Caddy must bind to a LAN-accessible interface (default 0.0.0.0).
    assert "KIROBI_PROXY_BIND_HOST" in compose
    assert "CADDY_HTTP_PORT" in compose and "CADDY_HTTPS_PORT" in compose
    assert "caddy:2-alpine" in compose


def test_tailscale_url_helper_exists_and_is_used_by_makefile():
    script = REPO_ROOT / "infra" / "scripts" / "tailscale-url.sh"
    makefile = (REPO_ROOT / "Makefile").read_text()
    assert script.is_file()
    assert "bash infra/scripts/tailscale-url.sh" in makefile
    assert "tailscale ip -4" in script.read_text()


# --- CORS in services -------------------------------------------------------
def test_auth_service_has_safe_cors_config():
    src = (REPO_ROOT / "services" / "auth" / "main.py").read_text()
    # The previous wildcard configuration would be silently rejected by
    # browsers when allow_credentials=True. Look for the actual middleware
    # invocation, not comments that document the old anti-pattern.
    assert "add_middleware(\n    CORSMiddleware,\n    **_cors_kwargs()" in src
    assert "KIROBI_PUBLIC_ORIGINS" in src
    assert "allow_origin_regex" in src
    assert "100\\.(6[4-9]|[7-9]\\d|1[0-1]\\d|12[0-7])" in src


def test_api_service_has_safe_cors_config():
    src = (REPO_ROOT / "services" / "api" / "main.py").read_text()
    assert "add_middleware(\n    CORSMiddleware,\n    **_cors_kwargs()" in src
    assert "KIROBI_PUBLIC_ORIGINS" in src
    assert "100\\.(6[4-9]|[7-9]\\d|1[0-1]\\d|12[0-7])" in src


# --- First-run user bootstrap ------------------------------------------------
def test_auth_service_seeds_default_user():
    src = (REPO_ROOT / "services" / "auth" / "main.py").read_text()
    assert "_ensure_default_user" in src
    assert "_ensure_schema" in src
    assert "KIROBI_DEFAULT_USER" in src
    assert "KIROBI_DEFAULT_PASSWORD" in src
    # Schema must be idempotent.
    assert "CREATE TABLE IF NOT EXISTS users" in src


def test_api_service_bootstraps_conversation_storage():
    src = (REPO_ROOT / "services" / "api" / "main.py").read_text()
    assert "async def _ensure_schema" in src
    assert "CREATE TABLE IF NOT EXISTS conversations" in src
    assert "CREATE TABLE IF NOT EXISTS messages" in src
    assert "CREATE TABLE IF NOT EXISTS file_uploads" in src
    assert "await _ensure_schema()" in src


def test_service_healthchecks_declare_requests_dependency():
    for service in ("auth", "api"):
        dockerfile = (REPO_ROOT / "services" / service / "Dockerfile").read_text()
        requirements = (REPO_ROOT / "services" / service / "requirements.txt").read_text()
        assert "import requests" in dockerfile
        assert "requests==" in requirements


def test_service_requirements_do_not_pin_python_as_a_package():
    for service in ("auth", "api"):
        requirements = (REPO_ROOT / "services" / service / "requirements.txt").read_text()
        assert "\npython==" not in requirements


def test_api_service_requirements_omit_unused_langchain_stack():
    src = (REPO_ROOT / "services" / "api" / "main.py").read_text()
    requirements = (REPO_ROOT / "services" / "api" / "requirements.txt").read_text()
    assert "langchain" not in src
    assert "\nlangchain==" not in requirements
    assert "\nlangchain-community==" not in requirements


def test_auth_requirements_include_email_validator_for_emailstr_models():
    src = (REPO_ROOT / "services" / "auth" / "main.py").read_text()
    requirements = (REPO_ROOT / "services" / "auth" / "requirements.txt").read_text()
    assert "EmailStr" in src
    assert "email-validator==" in requirements


def test_auth_requirements_pin_bcrypt_for_passlib_compatibility():
    requirements = (REPO_ROOT / "services" / "auth" / "requirements.txt").read_text()
    assert "passlib[bcrypt]==1.7.4" in requirements
    assert "bcrypt==4.0.1" in requirements


def test_password_reset_maintenance_flow_exists():
    makefile = (REPO_ROOT / "Makefile").read_text()
    script = (REPO_ROOT / "infra" / "scripts" / "reset-default-password.sh").read_text()
    assert "reset-default-password" in makefile
    assert "infra/scripts/reset-default-password.sh" in makefile
    assert "KIROBI_DEFAULT_USER" in script
    assert "KIROBI_DEFAULT_PASSWORD" in script
    assert "--dry-run" in script


def test_auth_session_storage_matches_text_device_info_schema():
    src = (REPO_ROOT / "services" / "auth" / "main.py").read_text()
    assert "import json" in src
    assert "json.dumps({})" in src


def test_auth_audit_log_details_are_serialized_before_insert():
    src = (REPO_ROOT / "services" / "auth" / "main.py").read_text()
    assert "json.dumps(details)" in src


def test_api_message_json_fields_are_serialized_and_normalized():
    src = (REPO_ROOT / "services" / "api" / "main.py").read_text()
    assert "import json" in src
    assert "json.dumps(message_data.attachments or [])" in src
    assert "def _message_from_row" in src
    assert "data[\"attachments\"] = _json_field(data.get(\"attachments\"), [])" in src
    assert "data[\"metadata\"] = _json_field(data.get(\"metadata\"), {})" in src


def test_api_ollama_call_has_model_fallback():
    src = (REPO_ROOT / "services" / "api" / "main.py").read_text()
    assert 'OLLAMA_FALLBACK_MODEL = "llama3.1:8b"' in src
    assert 'if response.status_code == 404 and model != OLLAMA_FALLBACK_MODEL:' in src
    assert 'response = await _chat_once(OLLAMA_FALLBACK_MODEL)' in src


# --- Next.js layout / config -------------------------------------------------
def test_next_layout_links_manifest_and_apple_meta():
    src = (REPO_ROOT / "apps" / "web" / "src" / "app" / "layout.tsx").read_text()
    assert "manifest: '/manifest.json'" in src
    assert "appleWebApp" in src
    assert "viewportFit: 'cover'" in src
    # Theme colour matches manifest.
    assert "#0f172a" in src


def test_next_config_pwa_setup_is_resilient():
    src = (REPO_ROOT / "apps" / "web" / "next.config.js").read_text()
    assert "next-pwa" in src
    assert "fallbacks" in src and "/offline.html" in src
    # Rewrite list must be guarded so `next build` does not crash without
    # AUTH_SERVICE_URL / API_SERVICE_URL.
    assert "buildRewrites" in src
    assert "process.env.AUTH_SERVICE_URL" in src


# --- Icon generator ---------------------------------------------------------
def test_icon_generator_runs(tmp_path):
    pytest.importorskip("PIL")
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build_pwa_icons", REPO_ROOT / "infra" / "scripts" / "build-pwa-icons.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    paths = mod.write_assets(tmp_path)
    names = {p.name for p in paths}
    assert {
        "icon.svg", "icon-192.png", "icon-512.png",
        "icon-192-maskable.png", "icon-512-maskable.png",
        "apple-touch-icon.png", "favicon.ico",
    }.issubset(names)
