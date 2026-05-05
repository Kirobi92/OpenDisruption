from pathlib import Path

from kirobi_core.backlog import Priority, generate_backlog, prioritize
from kirobi_core.scanner import scan_repository


def _mk(repo: Path, rel: str, content: str = "x") -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_backlog_flags_missing_readme(tmp_path):
    _mk(tmp_path, "services/foo/main.py", "print('hi')")
    scan = scan_repository(tmp_path)
    tasks = generate_backlog(scan)
    kinds = {t.kind for t in tasks}
    assert "missing-readme" in kinds


def test_backlog_flags_missing_tests(tmp_path):
    _mk(tmp_path, "kirobi_core/x.py", "x = 1")
    scan = scan_repository(tmp_path)
    tasks = generate_backlog(scan)
    assert any(t.kind == "missing-tests" for t in tasks)


def test_backlog_flags_placeholder_doc(tmp_path):
    _mk(tmp_path, "metadata/SHORT.md", "x")  # < 200 bytes
    scan = scan_repository(tmp_path)
    tasks = generate_backlog(scan)
    assert any(t.kind == "placeholder-readme" and "SHORT.md" in t.paths[0] for t in tasks)


def test_prioritize_orders_by_priority(tmp_path):
    _mk(tmp_path, "kirobi_core/x.py", "x = 1")  # triggers missing-tests (HIGH)
    _mk(tmp_path, "metadata/SHORT.md", "x")  # placeholder (LOW)
    scan = scan_repository(tmp_path)
    tasks = prioritize(generate_backlog(scan))
    priorities = [t.priority for t in tasks]
    # HIGH must appear before LOW.
    assert priorities.index(Priority.HIGH) < priorities.index(Priority.LOW)


def test_task_to_dict_is_serializable(tmp_path):
    import json

    _mk(tmp_path, "kirobi_core/x.py", "x = 1")
    scan = scan_repository(tmp_path)
    tasks = generate_backlog(scan)
    encoded = json.dumps([t.to_dict() for t in tasks])
    assert "missing-tests" in encoded
