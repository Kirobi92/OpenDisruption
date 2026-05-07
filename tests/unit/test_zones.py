from kirobi_core.zones import Zone, can_write, classify, filter_writable


def test_classify_top_level_readme_is_public():
    assert classify("README.md") is Zone.PUBLIC
    assert classify("CHANGELOG.md") is Zone.PUBLIC


def test_classify_workspace_paths():
    assert classify("kirobi_core/cli.py") is Zone.WORKSPACE
    assert classify("services/orchestrator/supervisor.py") is Zone.WORKSPACE
    assert classify("metadata/AGENTREGISTRY.md") is Zone.WORKSPACE
    assert classify("config/opencode/keycodi-agent.prompt.md") is Zone.WORKSPACE


def test_classify_family_private():
    assert classify("extracts/family-private/profile.json") is Zone.FAMILY_PRIVATE
    assert classify("experiences/family/notes.md") is Zone.FAMILY_PRIVATE


def test_classify_quarantine_and_inbox():
    assert classify("quarantine/foo.bin") is Zone.QUARANTINE
    assert classify("sources/inbox/x.pdf") is Zone.QUARANTINE


def test_classify_sacred():
    assert classify("sacred/handoff-only.md") is Zone.SACRED


def test_unknown_top_level_falls_back_to_sacred_for_safety():
    assert classify("totally_unknown_dir/data.bin") is Zone.SACRED


def test_can_write_allows_workspace_and_public():
    assert can_write("kirobi_core/cli.py").allowed is True
    assert can_write("README.md").allowed is True


def test_can_write_blocks_sacred_unless_approved():
    decision = can_write("sacred/secret.md")
    assert decision.allowed is False
    assert "approval" in decision.reason.lower()
    assert can_write("sacred/secret.md", approved=True).allowed is True


def test_filter_writable_strips_sensitive_paths():
    paths = [
        "README.md",
        "kirobi_core/cli.py",
        "extracts/family-private/secret.json",
        "sacred/secret.md",
        "quarantine/x",
    ]
    out = filter_writable(paths)
    assert "README.md" in out
    assert "kirobi_core/cli.py" in out
    assert "extracts/family-private/secret.json" not in out
    assert "sacred/secret.md" not in out
    assert "quarantine/x" not in out
