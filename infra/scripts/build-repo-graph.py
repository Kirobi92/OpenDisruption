#!/usr/bin/env python3
"""Build an integral repo graph: AQAL quadrants + Spiral Dynamics + edge types.

Walks the entire OpenDisruption repository (excluding node_modules / .git /
.venv / large build caches) and produces a JSON graph for the SvelteKit
3D viewer (apps/web-svelte/static/repo-graph.json).

For each file we emit a node with:
  - id           : repo-relative path
  - label        : basename (without ext)
  - dir          : top-level dir (apps, services, kidi, ...)
  - ext          : file extension
  - zone         : PUBLIC / WORKSPACE / FAMILY_PRIVATE / QUARANTINE (SACRED skipped)
  - quadrant     : AQAL — UL / UR / LL / LR
  - spiral       : Spiral Dynamics meme (beige / purple / red / blue /
                                          orange / green / yellow / turquoise)
  - size         : 1 + incoming-link count (centrality proxy)
  - tags         : optional frontmatter tags
  - agent        : optional frontmatter agent

Edges have a `type`:
  - wikilink     — `[[foo]]` in markdown → cyan rays
  - import       — Python `import` / `from x import` → violet rays
  - service-dep  — docker-compose `depends_on` → magenta rays
  - agent-call   — agent registry references → gold rays
  - zone-flow    — cross-zone import (anomaly highlight) → rose rays

Stdlib only. Honors CLAUDE.md §3: never read /sacred/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "apps" / "web-svelte" / "static" / "repo-graph.json"
LEGACY_OUTPUT = REPO_ROOT / "apps" / "web" / "public" / "repo-graph.json"

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", ".next", "__pycache__",
    ".pytest_cache", ".kirobi", "archive", "data", "models",
    ".obsidian", ".vscode", "external",
}
EXCLUDE_TOPLEVEL = {"sacred"}
INCLUDE_EXTS = {".md", ".py", ".ts", ".tsx", ".js", ".jsx", ".svelte",
                ".yml", ".yaml", ".toml", ".json", ".sh"}
MAX_FILE_BYTES = 256_000

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]+)?(?:\|([^\]]+))?\]\]")
PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", re.MULTILINE)
TS_IMPORT_RE = re.compile(
    r"""(?:^|\n)\s*(?:import|export)\s+(?:[^'"\n;]*?\sfrom\s+)?['"]([^'"]+)['"]"""
)
CADDY_REVERSE_RE = re.compile(r"reverse_proxy\s+(?:[^\s{]+\s+)?([a-zA-Z0-9_-]+):\d+")
TELEGRAM_HINT_RE = re.compile(r"TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID|telegram_bot|aiogram|python-telegram-bot", re.I)
SERVICE_HTTP_RE = re.compile(r"https?://([a-zA-Z][a-zA-Z0-9_-]+):\d+")
COMPOSE_DEP_RE = re.compile(r"^\s+depends_on:\s*\n((?:\s+-\s+\w+\s*\n)+)", re.MULTILINE)
COMPOSE_SERVICE_RE = re.compile(r"^\s{2}(\w[\w-]*):\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# AQAL quadrant heuristic by top-level directory
AQAL_BY_DIR = {
    "prompts": "UL", "sacred": "UL", "kirobi-core": "UL",
    "kirobi_core": "UR", "services": "UR", "apps": "UR",
    "kidi": "UR", "integrations": "UR", "agents": "LL",
    "docs": "LL", "experiences": "LL", "canon": "LL",
    "obsidian": "LL", "keycodi": "LL", "metadata": "LL",
    "clusters": "LL", "extracts": "LL", "research": "LL",
    "templates": "LL", "infra": "LR", ".github": "LR",
    ".opencode": "LR", ".claude": "LR", ".agents": "LR",
    "config": "LR", "tests": "UR",
}

# Per-file overrides (special AQAL homes)
AQAL_FILE_HINTS = {
    "AGENTS.md": "LL", "CLAUDE.md": "LL", "AGENT-SYSTEM-PROMPT.md": "UL",
    "PROJECT-CHARTER.md": "LL", "ROADMAP.md": "LL", "SECURITY.md": "LR",
    "docker-compose.yml": "LR", "Makefile": "LR", "install.sh": "LR",
}

SPIRAL_RULES = [
    ("turquoise", re.compile(r"keycodi|emergence|kidi/(engine|orchestra|aqal|integral)|holistic", re.I)),
    ("yellow", re.compile(r"\bkidi\b|integral|aqal|spiral|multi.?perspective|systems.?thinking", re.I)),
    ("green", re.compile(r"samira|mediation|family|community|empathy|heart", re.I)),
    ("orange", re.compile(r"roadmap|milestone|performance|benchmark|optimi[sz]e|build|test", re.I)),
    ("blue", re.compile(r"polic|governance|schema|registry|charter|standard|convention", re.I)),
    ("red", re.compile(r"boundary|prohibit|refuse|security|defense|threat", re.I)),
    ("purple", re.compile(r"sacred|tradition|experience|ritual|family.?private", re.I)),
    ("beige", re.compile(r"\.env|secret|credential|backup|disaster", re.I)),
]

ZONE_BY_PATH = [
    (re.compile(r"^sacred(/|$)"), "SACRED"),
    (re.compile(r"^extracts/family-private(/|$)|^experiences/family(/|$)|^canon/family(/|$)|^clusters/family(/|$)"), "FAMILY_PRIVATE"),
    (re.compile(r"^quarantine(/|$)|^sources/inbox(/|$)"), "QUARANTINE"),
    (re.compile(r"^extracts/public(/|$)|^canon/public(/|$)|^docs(/|$)"), "PUBLIC"),
]


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip().strip("\"'")
        if key == "tags" and value.startswith("["):
            value = [t.strip().strip("\"'") for t in value[1:-1].split(",") if t.strip()]
        out[key] = value
    return out


def classify_zone(rel: str, fm: dict) -> str:
    if (z := str(fm.get("zone", "")).upper()) in {"PUBLIC", "WORKSPACE", "FAMILY_PRIVATE", "QUARANTINE", "SACRED"}:
        return z
    for pattern, zone in ZONE_BY_PATH:
        if pattern.match(rel):
            return zone
    return "WORKSPACE"


def classify_quadrant(rel: str, fm: dict) -> str:
    if (q := str(fm.get("quadrant", "")).upper()) in {"UL", "UR", "LL", "LR"}:
        return q
    name = Path(rel).name
    if name in AQAL_FILE_HINTS:
        return AQAL_FILE_HINTS[name]
    top = rel.split("/", 1)[0]
    return AQAL_BY_DIR.get(top, "LR")


def classify_spiral(rel: str, fm: dict, text: str) -> str:
    if (s := str(fm.get("spiral", "")).lower()) in {"beige", "purple", "red", "blue", "orange", "green", "yellow", "turquoise"}:
        return s
    haystack = f"{rel}\n{text[:2048]}"
    for spiral, pattern in SPIRAL_RULES:
        if pattern.search(haystack):
            return spiral
    return "blue"


def normalise_wikilink(source_id: str, raw: str) -> str:
    target = raw.strip()
    if target.startswith(("./", "../")):
        base = Path(source_id).parent
        try:
            target = str((base / target).resolve().relative_to(REPO_ROOT))
        except (ValueError, OSError):
            pass
    return target.removesuffix(".md")


def extract_compose_deps(text: str) -> list[tuple[str, str]]:
    """Return list of (service, dependency) pairs from a docker-compose file."""
    edges: list[tuple[str, str]] = []
    services = COMPOSE_SERVICE_RE.findall(text)
    if not services:
        return edges
    # naive but works: split by service header, scan each block for depends_on lines
    blocks = re.split(r"(?m)^  (\w[\w-]*):\s*$", text)
    # blocks[0] is preamble, then alternating (name, body)
    for i in range(1, len(blocks), 2):
        name = blocks[i]
        body = blocks[i + 1] if i + 1 < len(blocks) else ""
        m = COMPOSE_DEP_RE.search(body)
        if not m:
            continue
        for dep_line in m.group(1).splitlines():
            dep = dep_line.strip().lstrip("-").strip()
            dep = dep.split(":", 1)[0].strip()
            if dep:
                edges.append((name, dep))
    return edges


def ts_import_to_node(spec: str, source_id: str, all_node_ids: set[str]) -> str | None:
    """Resolve a TS/JS/Svelte import specifier to an existing node id.

    Only repo-internal relative imports are kept. Bare specifiers (npm packages,
    `$lib`, `$app`) are dropped to avoid noise — they are not source-of-truth nodes.
    """
    if not spec or spec.startswith(("$", "@")) or not spec.startswith((".", "/")):
        return None
    src_dir = Path(source_id).parent
    target = (src_dir / spec).as_posix() if spec.startswith(".") else spec.lstrip("/")
    target = re.sub(r"/+", "/", target)
    while "/./" in target:
        target = target.replace("/./", "/")
    while "/../" in target:
        target = re.sub(r"[^/]+/\.\./", "", target, count=1)
    candidates = [
        target,
        f"{target}.ts", f"{target}.tsx", f"{target}.js", f"{target}.jsx", f"{target}.svelte",
        f"{target}/index.ts", f"{target}/index.js", f"{target}/+page.svelte",
    ]
    for cand in candidates:
        nid = cand.removesuffix(".md").removesuffix(".py")
        if nid in all_node_ids:
            return nid
        if cand in all_node_ids:
            return cand
    return None


def python_module_to_path(module: str, all_paths: set[str]) -> str | None:
    parts = module.split(".")
    candidates = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]
    for c in candidates:
        if c in all_paths:
            return c.removesuffix(".py").removesuffix("/__init__")
    return None


INCLUDE_FILENAMES = {"Caddyfile", "Dockerfile", "Makefile"}


def should_skip(path: Path, rel: str) -> bool:
    parts = rel.split("/")
    if any(p in EXCLUDE_DIRS for p in parts):
        return True
    if parts[0] in EXCLUDE_TOPLEVEL:
        return True
    if path.suffix not in INCLUDE_EXTS and path.name not in INCLUDE_FILENAMES:
        return True
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return True
    except OSError:
        return True
    return False


def build_graph(repo_root: Path) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    all_files: list[tuple[str, Path, str, dict]] = []

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = str(path.relative_to(repo_root))
        except ValueError:
            continue
        if should_skip(path, rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        fm = parse_frontmatter(text) if path.suffix == ".md" else {}
        zone = classify_zone(rel, fm)
        if zone == "SACRED":
            continue
        node_id = rel.removesuffix(path.suffix) if path.suffix in {".md", ".py"} else rel
        quadrant = classify_quadrant(rel, fm)
        spiral = classify_spiral(rel, fm, text)
        top = rel.split("/", 1)[0]
        nodes[node_id] = {
            "id": node_id,
            "label": path.stem,
            "dir": top,
            "ext": path.suffix.lstrip("."),
            "zone": zone,
            "quadrant": quadrant,
            "spiral": spiral,
            "agent": fm.get("agent", ""),
            "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
            "size": 1,
        }
        all_files.append((node_id, path, text, fm))

    py_paths = {f"{nid}.py" for nid, p, _, _ in all_files if p.suffix == ".py"}
    py_paths |= {f"{nid}/__init__.py" for nid, p, _, _ in all_files if p.suffix == ".py"}
    all_node_ids = set(nodes.keys())
    service_dirs = {nid.split("/")[1] for nid in nodes if nid.startswith("services/") and "/" in nid[len("services/"):]}

    for node_id, path, text, _fm in all_files:
        src_zone = nodes[node_id]["zone"]

        # Wikilinks (strip fenced code blocks first to avoid bash conditionals etc.)
        if path.suffix == ".md":
            stripped = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
            stripped = re.sub(r"`[^`\n]*`", "", stripped)
            for raw, _alias in WIKILINK_RE.findall(stripped):
                if any(c in raw for c in "${}=<>;|&\"\n") or len(raw) > 120:
                    continue
                target = normalise_wikilink(node_id, raw)
                edges.append({"source": node_id, "target": target, "type": "wikilink"})

        # Python imports — only repo-internal
        if path.suffix == ".py":
            for from_mod, plain_mod in PY_IMPORT_RE.findall(text):
                module = (from_mod or plain_mod).split(".")
                if not module or module[0] not in {"kirobi_core", "kidi", "services", "apps", "tests", "kirobi"}:
                    continue
                target = python_module_to_path(".".join(module), py_paths)
                if target and target != node_id:
                    edge_type = "zone-flow" if nodes.get(target, {}).get("zone") not in {src_zone, "PUBLIC"} else "import"
                    edges.append({"source": node_id, "target": target, "type": edge_type})

        # TS / JS / Svelte imports — only repo-internal relative paths
        if path.suffix in {".ts", ".tsx", ".js", ".jsx", ".svelte"}:
            seen_targets: set[str] = set()
            for spec in TS_IMPORT_RE.findall(text):
                target = ts_import_to_node(spec, node_id, all_node_ids)
                if target and target != node_id and target not in seen_targets:
                    seen_targets.add(target)
                    tgt_zone = nodes.get(target, {}).get("zone")
                    edge_type = "zone-flow" if tgt_zone and tgt_zone not in {src_zone, "PUBLIC"} else "import"
                    edges.append({"source": node_id, "target": target, "type": edge_type})

        # docker-compose service deps
        if path.name in {"docker-compose.yml", "docker-compose.override.yml"}:
            for svc, dep in extract_compose_deps(text):
                # try to resolve to services/<dep>
                dep_node = next((nid for nid in nodes if nid.startswith(f"services/{dep}/")), None)
                src_node = next((nid for nid in nodes if nid.startswith(f"services/{svc}/")), node_id)
                if dep_node:
                    edges.append({"source": src_node, "target": dep_node, "type": "service-dep"})

        # Caddy reverse_proxy → service edges (route topology)
        if "Caddyfile" in path.name or path.suffix == ".caddy":
            for svc in set(CADDY_REVERSE_RE.findall(text)):
                if svc in service_dirs:
                    dep_node = next((nid for nid in nodes if nid.startswith(f"services/{svc}/")), None)
                    if dep_node:
                        edges.append({"source": node_id, "target": dep_node, "type": "route"})
                # special case: web/web-svelte are app dirs not services/
                if svc in {"web", "web-svelte", "dashboard", "voice"}:
                    app_node = next((nid for nid in nodes if nid.startswith(f"apps/{svc}/")), None)
                    if app_node:
                        edges.append({"source": node_id, "target": app_node, "type": "route"})

        # Telegram bot bindings: any service/script that uses TELEGRAM_* connects to telegram service
        if path.suffix in {".py", ".ts", ".js", ".yml", ".yaml"} and TELEGRAM_HINT_RE.search(text):
            telegram_node = next((nid for nid in nodes if nid.startswith("services/telegram/")), None)
            if telegram_node and telegram_node != node_id and not node_id.startswith("services/telegram/"):
                edges.append({"source": telegram_node, "target": node_id, "type": "telegram-bind"})

        # Service-to-service HTTP calls (e.g. http://auth:8000) — runtime topology
        if path.suffix in {".py", ".ts", ".js", ".svelte"}:
            seen_http: set[str] = set()
            for svc in SERVICE_HTTP_RE.findall(text):
                if svc in seen_http or svc not in service_dirs:
                    continue
                seen_http.add(svc)
                dep_node = next((nid for nid in nodes if nid.startswith(f"services/{svc}/")), None)
                if dep_node and dep_node != node_id:
                    edges.append({"source": node_id, "target": dep_node, "type": "http-call"})

        # Agent registry: AGENTREGISTRY.md / AGENT-DECISION-MATRIX.md mention agents
        if path.name in {"AGENTREGISTRY.md", "AGENT-DECISION-MATRIX.md", "metadata/AGENTREGISTRY.md"}:
            for agent_name in re.findall(r"\b(kirobi-[a-z]+|hermes-\w+|samira-\w+|sineo-\w+|keycodi)\b", text):
                tgt = next((nid for nid in nodes if agent_name in nid), None)
                if tgt and tgt != node_id:
                    edges.append({"source": node_id, "target": tgt, "type": "agent-call"})

    # Materialise ghost nodes for unresolved wikilinks
    for edge in edges:
        if edge["target"] not in nodes:
            nodes[edge["target"]] = {
                "id": edge["target"],
                "label": Path(edge["target"]).name,
                "dir": "ghost",
                "ext": "",
                "zone": "WORKSPACE",
                "quadrant": "LL",
                "spiral": "blue",
                "agent": "",
                "tags": [],
                "size": 1,
            }

    # Centrality via incoming-link count
    for edge in edges:
        nodes[edge["target"]]["size"] += 1

    return {
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "links": edges,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "node_count": len(nodes),
            "link_count": len(edges),
            "edge_types": ["wikilink", "import", "service-dep", "agent-call",
                           "zone-flow", "route", "telegram-bind", "http-call"],
            "quadrants": {"UL": "Bewusstsein/Innen-Individuell", "UR": "Verhalten/Außen-Individuell",
                          "LL": "Kultur/Innen-Kollektiv", "LR": "Systeme/Außen-Kollektiv"},
            "spirals": ["beige", "purple", "red", "blue", "orange", "green", "yellow", "turquoise"],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build integral repo graph")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--also-legacy", action="store_true",
                        help=f"Also write to {LEGACY_OUTPUT} for the old Next viewer")
    parser.add_argument("--root", "-r", type=Path, default=REPO_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    graph = build_graph(args.root)
    payload = json.dumps(graph, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(payload[:2000])
        print(f"\n... ({graph['meta']['node_count']} nodes, {graph['meta']['link_count']} links)")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"[repo-graph] wrote {args.output}: "
          f"{graph['meta']['node_count']} nodes, {graph['meta']['link_count']} links")
    if args.also_legacy:
        LEGACY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        LEGACY_OUTPUT.write_text(payload + "\n", encoding="utf-8")
        print(f"[repo-graph] also wrote {LEGACY_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
