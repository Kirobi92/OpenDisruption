"""Pytest bootstrap for fresh-clone, stdlib-first test runs.

The baseline unit suite should stay runnable from a fresh clone with only
``pytest`` installed. Service-contract tests remain available when the
optional FastAPI/service-stack dependencies are present.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


_OPTIONAL_SERVICE_STACK_MODULES = (
    "asyncpg",
    "dotenv",
    "email_validator",
    "fastapi",
    "httpx",
    "jose",
    "multipart",
    "passlib",
    "qdrant_client",
    "uvicorn",
)
_MISSING_OPTIONAL_SERVICE_STACK_MODULES = tuple(
    module
    for module in _OPTIONAL_SERVICE_STACK_MODULES
    if importlib.util.find_spec(module) is None
)

_OPTIONAL_SERVICE_TESTS = {
    "tests/unit/test_analytics_service.py",
    "tests/unit/test_api_service.py",
    "tests/unit/test_auth_service.py",
    "tests/unit/test_embeddings_service.py",
    "tests/unit/test_image_generation_service.py",
    "tests/unit/test_ingest_service.py",
    "tests/unit/test_keycodi_telegram_responder.py",
    "tests/unit/test_media_processing_service.py",
    "tests/unit/test_model_routing_service.py",
    "tests/unit/test_music_generation_service.py",
    "tests/unit/test_personal_memory_pipeline_contract.py",
    "tests/unit/test_retrieval_service.py",
    "tests/unit/test_telegram_service.py",
    "tests/unit/test_video_generation_service.py",
}


def _register_hyphenated_service(dir_name: str, module_name: str) -> None:
    """Registriert einen Service mit Bindestrich als importierbares Namespace-Paket.

    Beispiel: services/model-routing/main.py → services.model_routing.main
    """
    service_dir = _ROOT / "services" / dir_name
    if not service_dir.exists():
        return

    # Paket-Stub für services.<module_name> anlegen
    pkg_name = f"services.{module_name}"
    if pkg_name not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader(pkg_name, loader=None, origin=str(service_dir))
        )
        pkg.__path__ = [str(service_dir)]  # type: ignore[attr-defined]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    # main.py wird absichtlich NICHT eager geladen, damit pytest auf einem
    # frischen Clone nicht an optionalen Service-Dependencies scheitert.


for _dir_name, _module_name in (
    ("model-routing", "model_routing"),
    ("image-generation", "image_generation"),
    ("media-processing", "media_processing"),
    ("music-generation", "music_generation"),
    ("video-generation", "video_generation"),
    ("analytics-service", "analytics_service"),
):
    _register_hyphenated_service(_dir_name, _module_name)


def pytest_ignore_collect(collection_path, path=None, config=None):  # type: ignore[no-untyped-def]
    """Skip optional service tests when the service stack deps are absent."""
    if not _MISSING_OPTIONAL_SERVICE_STACK_MODULES:
        return False

    try:
        relative = Path(str(collection_path)).resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return False
    return relative in _OPTIONAL_SERVICE_TESTS
