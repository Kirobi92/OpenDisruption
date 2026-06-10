from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "opendisruption_ultimate.py"


spec = importlib.util.spec_from_file_location("opendisruption_ultimate", SCRIPT)
ultimate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["opendisruption_ultimate"] = ultimate
spec.loader.exec_module(ultimate)


def test_status_contains_all_ultimate_domains() -> None:
    status = ultimate.build_status(REPO_ROOT)

    assert status["system"] == "OpenDisruption Ultimate"
    assert status["principles"]["local_first"] is True
    assert status["principles"]["family_private_never_cloud"] is True
    assert status["domains"]["kirobi_family"] == "ready"
    assert status["domains"]["luki_business"] == "ready"
    assert status["domains"]["shared_infra"] == "ready"
    assert status["domains"]["labs"] == "ready"
    assert status["domains"]["archive"] == "ready"
    assert status["capabilities"]["ingest"] == "planned"
    assert status["capabilities"]["retrieval"] == "planned"


def test_status_detects_graphify_and_lazycodex_harness() -> None:
    status = ultimate.build_status(REPO_ROOT)
    graph = ultimate.graphify_status(REPO_ROOT)

    assert "graph_knowledge" in status["capabilities"]
    assert "lazycodex_harness" in status["capabilities"]
    assert status["capabilities"]["graph_knowledge"] == "ready"
    assert graph["nodes"] > 0
    assert graph["edges"] > 0


def test_json_cli_is_machine_readable() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPT), "status", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["system"] == "OpenDisruption Ultimate"
    assert payload["domains"]["kirobi_family"] == "ready"
    assert "next_actions" in payload


def test_blueprint_cli_names_all_feature_planes() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPT), "blueprint"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "# OpenDisruption Ultimate" in result.stdout
    assert "Family AI Plane" in result.stdout
    assert "Business AI Plane" in result.stdout
    assert "Shared Infrastructure Plane" in result.stdout
    assert "Labs Plane" in result.stdout


def test_graph_cli_is_machine_readable() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPT), "graph", "--json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["nodes"] > 0
    assert payload["report_present"] is True
