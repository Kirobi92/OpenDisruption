#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]
CapabilityState = Literal["ready", "planned", "missing"]
log = logging.getLogger("opendisruption.ultimate")


class Principles(TypedDict):
    local_first: bool
    family_private_never_cloud: bool
    business_data_never_kirobi: bool
    runtime_data_outside_repo: bool
    caddy_single_entry: bool


class UltimateStatus(TypedDict):
    system: str
    version: str
    repo_root: str
    principles: Principles
    domains: dict[str, CapabilityState]
    capabilities: dict[str, CapabilityState]
    feature_planes: dict[str, list[str]]
    next_actions: list[str]


class GraphifyStatus(TypedDict):
    ready: bool
    nodes: int
    edges: int
    communities: int
    report_present: bool
    graph_path: str
    report_path: str


@dataclass(frozen=True, slots=True)
class PathCheck:
    name: str
    required_paths: tuple[str, ...]
    planned_when_missing: bool = False


DOMAIN_CHECKS: tuple[PathCheck, ...] = (
    PathCheck("kirobi_family", ("products/kirobi/README.md", "products/kirobi/canon")),
    PathCheck("luki_business", ("products/luki/README.md", "products/luki/knowledge", "products/luki/retrieval")),
    PathCheck("shared_infra", ("infra/README.md", "infra/caddy", "infra/qdrant", "infra/ollama")),
    PathCheck("labs", ("labs/README.md", "labs/mission-control", "labs/open-webui", "labs/hindsight")),
    PathCheck("archive", ("archive/README.md", "archive/opendisruption-v0.1-snapshot")),
)

CAPABILITY_CHECKS: tuple[PathCheck, ...] = (
    PathCheck("policy_gate", ("packages/policy-gate", "docs/security")),
    PathCheck("ingest", ("packages/ingest", "products/luki/source-docs/manifest.json")),
    PathCheck("retrieval", ("packages/retrieval", "products/luki/evals/v1/questions.json"), planned_when_missing=True),
    PathCheck("backup_restore", ("infra/backup/backup-datenspeicher.sh",)),
    PathCheck("graph_knowledge", ("graphify-out/graph.json",), planned_when_missing=True),
    PathCheck("agent_harness", ("docs/architecture-planning/09_next_agent_prompts.md",)),
)

LAZYCODEX_SKILLS: tuple[str, ...] = ("ulw-plan", "start-work", "ulw-loop")


def _state_for(root: Path, check: PathCheck) -> CapabilityState:
    present = all((root / item).exists() for item in check.required_paths)
    if present:
        return "ready"
    if check.planned_when_missing:
        return "planned"
    return "missing"


def _lazycodex_state(codex_home: Path) -> CapabilityState:
    omo_root = codex_home / "plugins" / "cache" / "sisyphuslabs" / "omo"
    for version_dir in omo_root.glob("*"):
        if all((version_dir / "skills" / skill / "SKILL.md").exists() for skill in LAZYCODEX_SKILLS):
            return "ready"
    return "planned"


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        msg = f"{path} must contain a JSON object"
        raise TypeError(msg)
    return payload


def graphify_status(root: Path = REPO_ROOT) -> GraphifyStatus:
    graph_path = root / "graphify-out" / "graph.json"
    report_path = root / "graphify-out" / "GRAPH_REPORT.md"
    if not graph_path.exists():
        return {
            "ready": False,
            "nodes": 0,
            "edges": 0,
            "communities": 0,
            "report_present": False,
            "graph_path": str(graph_path),
            "report_path": str(report_path),
        }
    payload = _read_json(graph_path)
    nodes = payload.get("nodes")
    links = payload.get("links")
    community_ids = {
        node.get("community")
        for node in nodes
        if isinstance(node, dict) and node.get("community") is not None
    } if isinstance(nodes, list) else set()
    return {
        "ready": True,
        "nodes": len(nodes) if isinstance(nodes, list) else 0,
        "edges": len(links) if isinstance(links, list) else 0,
        "communities": len(community_ids),
        "report_present": report_path.exists(),
        "graph_path": str(graph_path),
        "report_path": str(report_path),
    }


def _json_list_count(path: Path, key: str) -> int:
    if not path.exists():
        return 0
    payload = _read_json(path)
    items = payload.get(key)
    return len(items) if isinstance(items, list) else 0


def _feature_planes() -> dict[str, list[str]]:
    return {
        "family_ai": ["KIROBI PWA", "Telegram gateways", "Family canon", "FAMILY_PRIVATE zone"],
        "business_ai": ["LUKI Knowledge MVP", "Retrieval with sources", "Audit log", "50-question eval"],
        "shared_infra": ["Caddy", "Qdrant", "Ollama", "Postgres", "Monitoring", "Restic backup"],
        "agent_os": ["LazyCodex/OmO", "Graphify", "Hermes runtime", "Plan-to-work loops"],
        "labs": ["3D printing", "ComfyUI", "Open WebUI", "Flowise", "Hindsight", "Mission Control"],
        "security": ["Secret quarantine", "Tailscale boundary", "No raw-data cloud prompts", "Restore tests"],
    }


def build_status(root: Path = REPO_ROOT, codex_home: Path | None = None) -> UltimateStatus:
    resolved = root.resolve()
    resolved_codex_home = codex_home if codex_home is not None else Path.home() / ".codex"
    domains = {check.name: _state_for(resolved, check) for check in DOMAIN_CHECKS}
    capabilities = {check.name: _state_for(resolved, check) for check in CAPABILITY_CHECKS}
    graph = graphify_status(resolved)
    capabilities["graph_knowledge"] = "ready" if graph["ready"] and graph["nodes"] > 0 else "planned"
    manifest_count = _json_list_count(resolved / "products" / "luki" / "source-docs" / "manifest.json", "documents")
    eval_count = _json_list_count(resolved / "products" / "luki" / "evals" / "v1" / "questions.json", "questions")
    capabilities["ingest"] = "ready" if manifest_count > 0 else "planned"
    capabilities["retrieval"] = "ready" if eval_count >= 50 else "planned"
    capabilities["lazycodex_harness"] = _lazycodex_state(resolved_codex_home)
    graph_action = (
        "Keep OpenDisruption Graphify graph current after changes."
        if capabilities["graph_knowledge"] == "ready"
        else "Run `graphify update . --no-cluster` in OpenDisruption."
    )
    return {
        "system": "OpenDisruption Ultimate",
        "version": "0.1-ultimate-control-plane",
        "repo_root": str(resolved),
        "principles": {
            "local_first": True,
            "family_private_never_cloud": True,
            "business_data_never_kirobi": True,
            "runtime_data_outside_repo": True,
            "caddy_single_entry": True,
        },
        "domains": domains,
        "capabilities": capabilities,
        "feature_planes": _feature_planes(),
        "next_actions": [
            graph_action,
            "Promote status output into tools/doctor.",
            "Turn missing planned capabilities into phase-gated implementation tasks.",
        ],
    }


def render_blueprint(status: UltimateStatus) -> str:
    lines = [
        "# OpenDisruption Ultimate",
        "",
        "Local-first family, business, lab, and infrastructure AI OS.",
        "",
        "## Family AI Plane",
        "- KIROBI, Family canon, Telegram gateways, FAMILY_PRIVATE.",
        "",
        "## Business AI Plane",
        "- LUKI Knowledge MVP, source-bound retrieval, audit, evals.",
        "",
        "## Shared Infrastructure Plane",
        "- Caddy, Qdrant, Ollama, Postgres, monitoring, backup.",
        "",
        "## Agent OS Plane",
        "- LazyCodex/OmO, Graphify, Hermes runtime, verifiable work loops.",
        "",
        "## Labs Plane",
        "- 3D printing, ComfyUI, Open WebUI, Flowise, Hindsight, Mission Control.",
        "",
        "## Security Plane",
        "- Local-first, no FAMILY_PRIVATE cloud, runtime data outside repo, restore tests.",
        "",
        "## Capability Status",
    ]
    for name, state in sorted(status["domains"].items()):
        lines.append(f"- domain `{name}`: {state}")
    for name, state in sorted(status["capabilities"].items()):
        lines.append(f"- capability `{name}`: {state}")
    return "\n".join(lines) + "\n"


def render_graphify(status: GraphifyStatus) -> str:
    lines = [
        "# OpenDisruption Graphify",
        "",
        f"- ready: {status['ready']}",
        f"- nodes: {status['nodes']}",
        f"- edges: {status['edges']}",
        f"- communities: {status['communities']}",
        f"- report: {'present' if status['report_present'] else 'missing'}",
        "",
        "Refresh with:",
        "",
        "```bash",
        "graphify update .",
        "```",
    ]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opendisruption_ultimate")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=cmd_status)
    blueprint = sub.add_parser("blueprint")
    blueprint.set_defaults(handler=cmd_blueprint)
    graph = sub.add_parser("graph")
    graph.add_argument("--json", action="store_true")
    graph.set_defaults(handler=cmd_graph)
    return parser


def cmd_status(args: argparse.Namespace) -> int:
    status = build_status(REPO_ROOT)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0
    print(render_blueprint(status), end="")
    return 0


def cmd_blueprint(args: argparse.Namespace) -> int:
    del args
    print(render_blueprint(build_status(REPO_ROOT)), end="")
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    status = graphify_status(REPO_ROOT)
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0
    print(render_graphify(status), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return int(args.handler(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
