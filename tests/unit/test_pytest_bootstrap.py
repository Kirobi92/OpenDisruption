"""Contract tests for pytest bootstrap behavior."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_conftest_registers_hyphenated_services_without_importing_service_stack() -> None:
    """tests/conftest.py must not eagerly import optional service modules."""
    script = """
import builtins
import importlib.util
import pathlib
import sys

repo_root = pathlib.Path.cwd()
blocked = {"asyncpg", "fastapi", "httpx", "uvicorn"}
real_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] in blocked:
        raise RuntimeError(f"optional import attempted during bootstrap: {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import

spec = importlib.util.spec_from_file_location(
    "bootstrap_contract_conftest",
    repo_root / "tests" / "conftest.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert "services.model_routing" in sys.modules
assert "services.image_generation" in sys.modules
assert "services.media_processing" in sys.modules
assert "services.music_generation" in sys.modules
assert "services.video_generation" in sys.modules
assert "services.analytics_service" in sys.modules
assert "services.model_routing.main" not in sys.modules
assert "services.image_generation.main" not in sys.modules
assert "services.media_processing.main" not in sys.modules
assert "services.music_generation.main" not in sys.modules
assert "services.video_generation.main" not in sys.modules
assert "services.analytics_service.main" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
