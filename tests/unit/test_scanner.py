from pathlib import Path

from kirobi_core.scanner import scan_repository
from kirobi_core.zones import Zone


def _mk(repo: Path, rel: str, content: str = "x") -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_scan_classifies_files_by_zone(tmp_path):
    _mk(tmp_path, "README.md", "# hi")
    _mk(tmp_path, "kirobi_core/cli.py", "print('x')")
    _mk(tmp_path, "extracts/family-private/notes.md", "secret")
    _mk(tmp_path, "sacred/oath.md", "oath")
    _mk(tmp_path, "quarantine/foo.bin", "??")

    scan = scan_repository(tmp_path)

    by_path = {f.path: f for f in scan.files}
    assert by_path["README.md"].zone is Zone.PUBLIC
    assert by_path["kirobi_core/cli.py"].zone is Zone.WORKSPACE
    assert by_path["extracts/family-private/notes.md"].zone is Zone.FAMILY_PRIVATE
    assert by_path["sacred/oath.md"].zone is Zone.SACRED
    assert by_path["quarantine/foo.bin"].zone is Zone.QUARANTINE


def test_scan_skips_dot_git(tmp_path):
    _mk(tmp_path, ".git/HEAD", "ref")
    _mk(tmp_path, "README.md", "x")
    scan = scan_repository(tmp_path)
    assert all(not f.path.startswith(".git") for f in scan.files)


def test_scan_summary_counts_match(tmp_path):
    _mk(tmp_path, "README.md", "x")
    _mk(tmp_path, "kirobi_core/cli.py", "y" * 10)
    scan = scan_repository(tmp_path)
    summary = scan.summary()
    assert summary["total_files"] == len(scan.files)
    assert summary["total_bytes"] == sum(f.size for f in scan.files)
    assert summary["code_files"] >= 1
    assert summary["doc_files"] >= 1
