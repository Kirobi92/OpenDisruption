"""Tests for infra/scripts/build-vault-graph.py."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "infra" / "scripts" / "build-vault-graph.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_vault_graph", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_frontmatter_extracts_zone_and_tags():
    mod = _load()
    text = "---\nzone: WORKSPACE\ntags: [moc, index]\n---\n# Hello\n"
    fm = mod.parse_frontmatter(text)
    assert fm["zone"] == "WORKSPACE"
    assert fm["tags"] == ["moc", "index"]


def test_parse_frontmatter_returns_empty_for_no_frontmatter():
    mod = _load()
    assert mod.parse_frontmatter("# Just a heading\n") == {}


def test_normalise_link_strips_md_suffix():
    mod = _load()
    assert mod.normalise_link("a/b", "Some Note") == "Some Note"
    assert mod.normalise_link("a/b", "Some Note.md") == "Some Note"


def test_build_graph_emits_nodes_and_links(tmp_path):
    mod = _load()
    vault = tmp_path / "obsidian" / "vault"
    vault.mkdir(parents=True)
    (vault / "alpha.md").write_text(
        "---\nzone: WORKSPACE\ntags: [a]\n---\nLink to [[beta]] and [[gamma|G]].\n",
        encoding="utf-8",
    )
    (vault / "beta.md").write_text(
        "---\nzone: WORKSPACE\n---\nBack to [[alpha]].\n", encoding="utf-8"
    )
    graph = mod.build_graph(tmp_path)

    ids = {n["id"] for n in graph["nodes"]}
    assert "obsidian/vault/alpha" in ids
    assert "obsidian/vault/beta" in ids
    # Ghost target should be materialised.
    assert "gamma" in ids

    assert graph["meta"]["node_count"] == len(graph["nodes"])
    assert graph["meta"]["link_count"] == len(graph["links"])
    assert graph["meta"]["link_count"] == 3


def test_build_graph_skips_sacred_zone(tmp_path):
    mod = _load()
    vault = tmp_path / "obsidian" / "vault"
    vault.mkdir(parents=True)
    (vault / "secret.md").write_text(
        "---\nzone: SACRED\n---\nDo not index.\n", encoding="utf-8"
    )
    (vault / "public.md").write_text(
        "---\nzone: WORKSPACE\n---\nVisible.\n", encoding="utf-8"
    )
    graph = mod.build_graph(tmp_path)
    ids = {n["id"] for n in graph["nodes"]}
    assert "obsidian/vault/secret" not in ids
    assert "obsidian/vault/public" in ids


def test_main_writes_output(tmp_path):
    mod = _load()
    vault = tmp_path / "obsidian" / "vault"
    vault.mkdir(parents=True)
    (vault / "x.md").write_text("---\nzone: WORKSPACE\n---\n[[y]]\n", encoding="utf-8")
    out = tmp_path / "out.json"
    rc = mod.main(["--output", str(out), "--root", str(tmp_path)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["meta"]["node_count"] >= 2
