import json

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
    data = json.loads(out)
    assert data["total_files"] >= 1


def test_cli_backlog_outputs_list(tmp_path, capsys):
    (tmp_path / "kirobi_core").mkdir()
    (tmp_path / "kirobi_core" / "x.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["backlog", "--repo-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    items = json.loads(out)
    assert isinstance(items, list)


def test_cli_ingest_manifest_outputs_zone_gated_json(tmp_path, capsys):
    (tmp_path / "README.md").write_text("public", encoding="utf-8")
    (tmp_path / "sacred").mkdir()
    (tmp_path / "sacred" / "oath.md").write_text("sacred", encoding="utf-8")

    rc = main([
        "ingest-manifest",
        "--repo-root",
        str(tmp_path),
        "README.md",
        "sacred/oath.md",
    ])
    out = capsys.readouterr().out

    assert rc == 0
    data = json.loads(out)
    by_path = {entry["path"]: entry for entry in data["entries"]}
    assert by_path["README.md"]["action"] == "stage"
    assert by_path["sacred/oath.md"]["action"] == "block"
    assert by_path["sacred/oath.md"]["zone"] == "SACRED"


def test_cli_ingest_manifest_writes_jsonl_output(tmp_path, capsys):
    (tmp_path / "README.md").write_text("public", encoding="utf-8")

    rc = main([
        "ingest-manifest",
        "--repo-root",
        str(tmp_path),
        "--output",
        "metadata/personal-memory/manifests/latest.jsonl",
        "README.md",
    ])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Manifest written to:" in out
    written = tmp_path / "metadata/personal-memory/manifests/latest.jsonl"
    lines = written.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["path"] == "README.md"


def test_cli_ingest_manifest_blocks_protected_output(tmp_path, capsys):
    (tmp_path / "README.md").write_text("public", encoding="utf-8")
    (tmp_path / "sacred").mkdir()
    protected = tmp_path / "sacred" / "manifest.json"
    protected.write_text("keep", encoding="utf-8")

    rc = main([
        "ingest-manifest",
        "--repo-root",
        str(tmp_path),
        "--output",
        "sacred/manifest.json",
        "README.md",
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert "blocked" in captured.err
    assert protected.read_text(encoding="utf-8") == "keep"


def test_cli_autonomous_once_dry_run(tmp_path, capsys):
    (tmp_path / "kirobi_core").mkdir()
    (tmp_path / "kirobi_core" / "x.py").write_text("x = 1\n", encoding="utf-8")
    rc = main(["autonomous-once", "--repo-root", str(tmp_path), "--no-report"])
    assert rc == 0
    payload = capsys.readouterr().out
    assert '"dry_run": true' in payload
