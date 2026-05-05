from kirobi_core.cli import main


def test_cli_version(capsys):
    rc = main(["version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "kirobi_core" in out


def test_cli_doctor_runs(tmp_path, capsys):
    rc = main(["doctor", "--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Kirobi Doctor" in out
    # Some checks will warn / fail on an empty tmp_path; rc may be 2.
    assert rc in (0, 2)


def test_cli_scan_outputs_json(tmp_path, capsys):
    (tmp_path / "README.md").write_text("hi", encoding="utf-8")
    rc = main(["scan", "--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    import json

    data = json.loads(out)
    assert data["total_files"] >= 1


def test_cli_backlog_outputs_list(tmp_path, capsys):
    (tmp_path / "kirobi_core").mkdir()
    (tmp_path / "kirobi_core" / "x.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["backlog", "--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    import json

    items = json.loads(out)
    assert isinstance(items, list)


def test_cli_autonomous_once_dry_run(tmp_path, capsys):
    (tmp_path / "kirobi_core").mkdir()
    (tmp_path / "kirobi_core" / "x.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["autonomous-once", "--repo-root", str(tmp_path), "--no-report"])
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"dry_run": true' in payload
