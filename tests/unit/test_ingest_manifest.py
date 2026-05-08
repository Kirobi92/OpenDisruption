import json
import hashlib
from pathlib import Path

from kirobi_core.ingest_manifest import (
    build_manifest,
    decide_ingest_action,
    render_manifest_json,
    render_manifest_jsonl,
    write_manifest_output,
)
from kirobi_core.zones import Zone


def _mk(repo: Path, rel: str, content: str = "x") -> Path:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_decide_ingest_action_stages_only_public_and_workspace() -> None:
    assert decide_ingest_action(Zone.PUBLIC)[0] == "stage"
    assert decide_ingest_action(Zone.WORKSPACE)[0] == "stage"
    assert decide_ingest_action(Zone.FAMILY_PRIVATE)[0] == "block"
    assert decide_ingest_action(Zone.QUARANTINE)[0] == "block"
    assert decide_ingest_action(Zone.SACRED)[0] == "block"


def test_build_manifest_is_metadata_only_and_blocks_sensitive_zones(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    _mk(tmp_path, "kirobi_core/cli.py", "workspace")
    _mk(tmp_path, "extracts/family-private/notes.md", "family")
    _mk(tmp_path, "sources/inbox/upload.txt", "untrusted")
    _mk(tmp_path, "sacred/oath.md", "sacred")

    manifest = build_manifest(
        tmp_path,
        [
            "README.md",
            "kirobi_core/cli.py",
            "extracts/family-private/notes.md",
            "sources/inbox/upload.txt",
            "sacred/oath.md",
        ],
    )

    by_path = {entry.path: entry for entry in manifest.entries}
    assert by_path["README.md"].action == "stage"
    assert by_path["kirobi_core/cli.py"].action == "stage"
    assert by_path["extracts/family-private/notes.md"].action == "block"
    assert by_path["sources/inbox/upload.txt"].action == "block"
    assert by_path["sacred/oath.md"].action == "block"
    assert by_path["sacred/oath.md"].zone is Zone.SACRED
    assert all(not hasattr(entry, "content") for entry in manifest.entries)


def test_build_manifest_blocks_paths_outside_repo(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    manifest = build_manifest(tmp_path, [outside])

    assert len(manifest.entries) == 1
    entry = manifest.entries[0]
    assert entry.action == "block"
    assert entry.zone is Zone.SACRED
    assert "outside repository" in entry.reason


def test_build_manifest_expands_directories_without_reading_contents(tmp_path: Path) -> None:
    _mk(tmp_path, "docs/a.md", "public")
    _mk(tmp_path, "docs/nested/b.md", "public")
    _mk(tmp_path, "docs/.git/HEAD", "ignored")

    manifest = build_manifest(tmp_path, ["docs"])
    paths = [entry.path for entry in manifest.entries]

    assert paths == ["docs/a.md", "docs/nested/b.md"]
    assert all(entry.action == "stage" for entry in manifest.entries)


def test_render_manifest_json_is_machine_readable(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    manifest = build_manifest(tmp_path, ["README.md"])

    data = json.loads(render_manifest_json(manifest))

    assert data["total_files"] == 1
    assert data["by_action"] == {"stage": 1}
    assert data["entries"][0]["path"] == "README.md"


def test_stage_entries_include_hash_and_mime_only_for_allowed_zones(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    _mk(tmp_path, "sacred/oath.md", "sacred")

    manifest = build_manifest(tmp_path, ["README.md", "sacred/oath.md"])

    by_path = {entry.path: entry.to_dict() for entry in manifest.entries}
    assert by_path["README.md"]["sha256"] == hashlib.sha256(b"public").hexdigest()
    assert "mime_type" in by_path["README.md"]
    assert "sha256" not in by_path["sacred/oath.md"]
    assert "mime_type" not in by_path["sacred/oath.md"]


def test_markdown_frontmatter_can_raise_public_path_to_workspace(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        "docs/workspace-note.md",
        "---\nzone: WORKSPACE\n---\n# Workspace note\n",
    )

    manifest = build_manifest(tmp_path, ["docs/workspace-note.md"])

    entry = manifest.entries[0]
    assert entry.zone is Zone.WORKSPACE
    assert entry.action == "stage"
    assert entry.sha256 is not None


def test_markdown_frontmatter_is_not_read_for_blocked_path_zone(tmp_path: Path) -> None:
    _mk(
        tmp_path,
        "sacred/fake-public.md",
        "---\nzone: PUBLIC\n---\n# Must stay sacred\n",
    )

    manifest = build_manifest(tmp_path, ["sacred/fake-public.md"])

    entry = manifest.entries[0]
    assert entry.zone is Zone.SACRED
    assert entry.action == "block"
    assert entry.sha256 is None


def test_render_manifest_jsonl_outputs_one_entry_per_line(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    _mk(tmp_path, "kirobi_core/example.py", "print('x')\n")
    manifest = build_manifest(tmp_path, ["README.md", "kirobi_core/example.py"])

    lines = render_manifest_jsonl(manifest).splitlines()

    assert len(lines) == 2
    assert {json.loads(line)["path"] for line in lines} == {
        "README.md",
        "kirobi_core/example.py",
    }


def test_write_manifest_output_allows_workspace_json(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    manifest = build_manifest(tmp_path, ["README.md"])

    output = write_manifest_output(
        tmp_path,
        manifest,
        "metadata/personal-memory/manifests/latest.json",
    )

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["entries"][0]["path"] == "README.md"


def test_write_manifest_output_blocks_protected_path_without_overwrite(tmp_path: Path) -> None:
    _mk(tmp_path, "README.md", "public")
    protected = _mk(tmp_path, "sacred/manifest.json", "do not overwrite")
    manifest = build_manifest(tmp_path, ["README.md"])

    try:
        write_manifest_output(tmp_path, manifest, "sacred/manifest.json")
    except PermissionError as exc:
        assert "blocked" in str(exc)
    else:  # pragma: no cover - documents the expected fail-closed branch
        raise AssertionError("protected output path was not blocked")
    assert protected.read_text(encoding="utf-8") == "do not overwrite"
