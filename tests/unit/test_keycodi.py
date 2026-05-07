import json
from pathlib import Path

from kirobi_core.cli import main
from kirobi_core.keycodi import KEYCODI_NAME, plan_mission, render_text


REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed(repo: Path) -> None:
    (repo / "README.md").write_text("hi", encoding="utf-8")
    (repo / "kirobi_core").mkdir()
    (repo / "kirobi_core" / "x.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "metadata").mkdir()
    (repo / "metadata" / "AGENTREGISTRY.md").write_text(
        """## 1. kirobi-architect
**Rolle:** Architect
**Modell:** llama3.1:8b
**Zone-Zugriff:** PUBLIC, WORKSPACE

## 2. kirobi-coder
**Rolle:** Coder
**Modell:** qwen2.5-coder:32b
**Zone-Zugriff:** PUBLIC, WORKSPACE

## 3. kirobi-ops
**Rolle:** Ops
**Modell:** llama3.1:8b
**Zone-Zugriff:** PUBLIC, WORKSPACE

## 4. kirobi-observer
**Rolle:** Observer
**Modell:** mistral:7b
**Zone-Zugriff:** PUBLIC, WORKSPACE

## 5. creative-agent
**Rolle:** Creative
**Modell:** llama3.1:8b
**Zone-Zugriff:** PUBLIC, WORKSPACE
""",
        encoding="utf-8",
    )


def test_keycodi_plan_delegates_opencode_mission(tmp_path):
    _seed(tmp_path)
    plan = plan_mission(
        tmp_path,
        mission="Baue opencode als KeyCodi Coding Orchestrator mit emotionaler UX",
        limit=3,
    )

    payload = plan.to_dict()
    agents = {delegation["agent"] for delegation in payload["delegations"]}
    assert payload["name"] == KEYCODI_NAME
    assert "opencode" in payload["mission"]
    assert "kirobi-architect" in agents
    assert "kirobi-coder" in agents
    assert "kirobi-ops" in agents
    assert "creative-agent" in agents
    assert payload["opencode_handoff"]["status"] == "prepared_requires_model_approval"


def test_keycodi_plan_carries_safety_gates_and_no_dangerous_opencode_flag(tmp_path):
    _seed(tmp_path)
    plan = plan_mission(tmp_path, mission="KeyCodi security hardening")
    payload = plan.to_dict()
    joined = json.dumps(payload, ensure_ascii=False)
    assert "SACRED" in joined
    assert "cloud" in joined.lower()
    assert "dangerously-skip-permissions" not in joined


def test_keycodi_text_render_contains_handoff(tmp_path):
    _seed(tmp_path)
    text = render_text(plan_mission(tmp_path, mission="KeyCodi first act"))
    assert KEYCODI_NAME in text
    assert "Opencode handoff" in text
    assert "keycodi-opencode.sh --dry-run" in text


def test_cli_keycodi_outputs_json(tmp_path, capsys):
    _seed(tmp_path)
    rc = main(["keycodi", "--repo-root", str(tmp_path), "--json", "KeyCodi", "first", "act"])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["name"] == KEYCODI_NAME
    assert payload["mission"] == "KeyCodi first act"


def test_opencode_config_defaults_to_local_first_keycodi():
    config = json.loads((REPO_ROOT / "opencode.json").read_text())
    assert config["default_agent"] == "keycodi"
    assert config["permission"]["webfetch"] == "ask"

    remote_mcp_servers = [
        server for server in config["mcp"].values()
        if server.get("type") == "remote"
    ]
    assert remote_mcp_servers
    assert all(server.get("enabled") is False for server in remote_mcp_servers)


def test_keycodi_agent_keeps_external_and_shell_tools_gated():
    src = (REPO_ROOT / ".opencode" / "agents" / "keycodi.md").read_text()
    assert "  bash: ask" in src
    assert "  webfetch: ask" in src
    assert "  bash: allow" not in src
    assert "  webfetch: allow" not in src


def test_keycodi_launcher_uses_keycodi_agent_and_cloud_gate():
    src = (REPO_ROOT / "infra" / "scripts" / "keycodi-opencode.sh").read_text()
    assert "opencode run --agent keycodi" in src
    assert "opencode run --agent build" not in src
    assert "Refusing cloud-looking model" in src
    assert "dangerously-skip-permissions" not in src