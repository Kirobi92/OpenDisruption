from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "luki_qdrant_bootstrap.py"

spec = importlib.util.spec_from_file_location("luki_qdrant_bootstrap", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["luki_qdrant_bootstrap"] = bootstrap
spec.loader.exec_module(bootstrap)


def test_collection_payload_matches_nomic_embedding_size() -> None:
    payload = bootstrap.collection_payload(768)

    assert payload["vectors"]["size"] == 768
    assert payload["vectors"]["distance"] == "Cosine"


def test_qdrant_config_is_local_and_allowlisted() -> None:
    config = bootstrap.load_qdrant_config()

    assert config.collection == "luki_knowledge_v1"
    assert config.dimensions == 768
    assert config.qdrant_url == "http://127.0.0.1:6333"
    assert config.allowed_collections == ("luki_knowledge_v1",)
