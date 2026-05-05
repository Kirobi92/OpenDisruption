from kirobi_core.audit import AuditLogger


def test_audit_logger_writes_jsonl(tmp_path):
    log_path = tmp_path / "core-events.log"
    audit = AuditLogger(log_path)
    audit.log("test.event", actor="kirobi-core", zone="WORKSPACE", data={"k": "v"})
    audit.log("test.other", data={"password": "supersecret", "nested": {"api_key": "x"}})

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    import json

    first = json.loads(lines[0])
    assert first["action"] == "test.event"
    assert first["actor"] == "kirobi-core"
    assert first["zone"] == "WORKSPACE"
    assert first["data"] == {"k": "v"}

    second = json.loads(lines[1])
    assert second["data"]["password"] == "***REDACTED***"
    assert second["data"]["nested"]["api_key"] == "***REDACTED***"


def test_audit_logger_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "deep" / "dir" / "events.log"
    audit = AuditLogger(log_path)
    audit.log("x")
    assert log_path.exists()
