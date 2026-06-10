from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "luki_mvp_server.py"

spec = importlib.util.spec_from_file_location("luki_mvp_server", SCRIPT)
luki = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["luki_mvp_server"] = luki
spec.loader.exec_module(luki)


def test_luki_config_enforces_local_only_policy() -> None:
    config = luki.load_config()
    payload = luki.status_payload(config)

    assert config.collection == "luki_knowledge_v1"
    assert config.allow_cloud is False
    assert payload["ready"] is True
    assert payload["audit_enabled"] is True


def test_answer_refuses_without_retrieval_sources_and_writes_hash_audit(tmp_path: Path) -> None:
    config = luki.LukiConfig(
        collection="luki_knowledge_v1",
        allowed_collections=("luki_knowledge_v1",),
        allow_cloud=False,
        audit_enabled=True,
        data_root=tmp_path,
        secrets_file=tmp_path / "secrets" / "luki.env",
    )
    now = datetime(2026, 6, 9, 12, 0, tzinfo=UTC)

    response = luki.answer_question({"question": "Welche Artikelregeln gelten?"}, config, now)

    assert response["sources"] == []
    assert "Ich weiß es nicht" in response["answer"]
    audit_file = tmp_path / "luki" / "audit" / "2026-06" / "luki-audit-2026-06-09.jsonl"
    record = json.loads(audit_file.read_text(encoding="utf-8").strip())
    assert record["collection"] == "luki_knowledge_v1"
    assert record["source_ids"] == []
    assert "Welche Artikelregeln" not in audit_file.read_text(encoding="utf-8")
    assert oct(audit_file.stat().st_mode & 0o777) == "0o600"


def test_status_does_not_expose_runtime_paths() -> None:
    payload = luki.status_payload(luki.load_config())

    assert "source_manifest" not in payload
    assert "secrets_file" not in payload
    assert payload["source_manifest_present"] is True
    serialized = json.dumps(payload)
    assert "/Datenspeicher" not in serialized
    assert "luki.env" not in serialized


def test_config_rejects_collection_outside_allowlist(tmp_path: Path) -> None:
    config_path = tmp_path / "luki.json"
    config_path.write_text(
        json.dumps(
            {
                "collection": "kirobi_private",
                "policy": {"allow_cloud": False, "allowed_collections": ["luki_knowledge_v1"]},
                "audit": {"enabled": True},
                "runtime": {"data_root": str(tmp_path), "secrets_file": str(tmp_path / "luki.env")},
            }
        ),
        encoding="utf-8",
    )

    try:
        luki.load_config(config_path)
    except luki.RuntimeBoundaryError:
        return
    raise AssertionError("collection outside allowlist should fail")


def test_audit_rejects_repo_data_root() -> None:
    config = luki.LukiConfig(
        collection="luki_knowledge_v1",
        allowed_collections=("luki_knowledge_v1",),
        allow_cloud=False,
        audit_enabled=True,
        data_root=REPO_ROOT,
        secrets_file=REPO_ROOT / "fake.env",
    )

    try:
        luki.answer_question({"question": "Test"}, config, datetime(2026, 6, 9, 12, 0, tzinfo=UTC))
    except luki.RuntimeBoundaryError:
        return
    raise AssertionError("audit writes inside repo should fail")


def test_graphify_payload_is_first_class_status() -> None:
    payload = luki.graphify_payload(REPO_ROOT)

    assert payload["ready"] is True
    assert payload["nodes"] > 0
    assert payload["edges"] > 0
