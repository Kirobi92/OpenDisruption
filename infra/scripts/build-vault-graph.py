#!/usr/bin/env python3
"""Build a JSON graph of the Obsidian vault for the web /graph route.

Walks `obsidian/**/*.md`, extracts `[[wikilinks]]` and YAML frontmatter
(zone, tags, agent), and emits `apps/web/public/graph.json` with shape:

    {
      "nodes": [{ "id": str, "label": str, "group": str, "zone": str, "size": int }],
      "links": [{ "source": str, "target": str }],
      "meta": { "generated_at": iso8601, "node_count": int, "link_count": int }
    }

Node IDs are repo-relative paths without `.md` suffix to match how
Obsidian resolves links. Stdlib only — no external deps.

Zone classification follows CLAUDE.md §2: nothing under SACRED is read.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VAULT_DIRS = ["obsidian"]
DEFAULT_OUTPUT = REPO_ROOT / "apps" / "web" / "public" / "graph.json"

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|([^\]]+))?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    """Lightweight YAML frontmatter parser (zone/tags/agent only)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    out: dict = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip().strip("\"'")
        if key == "tags" and value.startswith("["):
            value = [t.strip().strip("\"'") for t in value[1:-1].split(",") if t.strip()]
        if key in {"zone", "tags", "agent", "phase"}:
            out[key] = value
    return out


def normalise_link(source_id: str, raw: str) -> str:
    """Resolve `[[../foo|bar]]` style relative wikilinks to a vault-style id."""
    target = raw.strip()
    if target.startswith(("./", "../")):
        base = Path(source_id).parent
        try:
            resolved = (base / target).resolve().relative_to(Path(".").resolve())
            target = str(resolved)
        except ValueError:
            pass
    return target.removesuffix(".md")


def build_graph(repo_root: Path) -> dict:
    nodes: dict[str, dict] = {}
    links: list[dict] = []

    for vault_name in VAULT_DIRS:
        vault = repo_root / vault_name
        if not vault.exists():
            continue
        for md in sorted(vault.rglob("*.md")):
            rel = md.relative_to(repo_root)
            node_id = str(rel.with_suffix(""))
            text = md.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            zone = (fm.get("zone") or "WORKSPACE").upper()
            if zone == "SACRED":
                continue
            group = rel.parts[1] if len(rel.parts) > 1 else "root"
            label = md.stem
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "group": group,
                "zone": zone,
                "agent": fm.get("agent", ""),
                "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
                "size": 1,
            }
            for raw, _alias in WIKILINK_RE.findall(text):
                target_id = normalise_link(node_id, raw)
                links.append({"source": node_id, "target": target_id})

    # Materialise link targets that don't exist as files (still useful as ghost nodes).
    for link in links:
        target = link["target"]
        if target not in nodes:
            nodes[target] = {
                "id": target,
                "label": Path(target).name,
                "group": "ghost",
                "zone": "WORKSPACE",
                "agent": "",
                "tags": [],
                "size": 1,
            }

    # Inflate node size by incoming-link count (proxy for centrality).
    for link in links:
        nodes[link["target"]]["size"] += 1

    return {
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "links": links,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "node_count": len(nodes),
            "link_count": len(links),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build vault graph JSON")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--root", "-r", type=Path, default=REPO_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    graph = build_graph(args.root)
    payload = json.dumps(graph, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(payload)
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
    print(
        f"[vault-graph] wrote {args.output.relative_to(args.root)}: "
        f"{graph['meta']['node_count']} nodes, {graph['meta']['link_count']} links"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
