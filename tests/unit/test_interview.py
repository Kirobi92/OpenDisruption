from kirobi_core.config import ConfigStore
from kirobi_core.interview import (
    DEFAULT_QUESTIONS,
    derive_config,
    run_and_save,
    run_interview,
    scripted_input,
)
from kirobi_core.zones import Zone


def test_run_interview_uses_defaults_for_empty_input():
    answers = scripted_input([""] * len(DEFAULT_QUESTIONS))
    public, sensitive = run_interview(input_fn=answers, output_fn=lambda _l: None)
    # Default for primary_goal is 'familie'.
    assert public["primary_goal"] == "familie"
    assert public["autonomy_level"] == "dry-run"
    # Sensitive answers default to empty string.
    assert sensitive["family_members"] == ""


def test_derive_config_picks_priority_agents():
    cfg = derive_config({"primary_goal": "business", "autonomy_level": "dry-run"})
    assert "enterprise-agent" in cfg["priority_agents"]
    assert cfg["default_dry_run"] is True


def test_derive_config_execute_disables_dry_run():
    cfg = derive_config({"primary_goal": "lernen", "autonomy_level": "execute-with-approval"})
    assert cfg["default_dry_run"] is False


def test_run_and_save_writes_profile_and_sensitive(tmp_path):
    store = ConfigStore(tmp_path)
    answers = ["Sven", "familie", "linux", "medium", "22:00-07:00", "dry-run", "nein",
               "Sven, Samira", "geheim"]
    path = run_and_save(
        store,
        input_fn=scripted_input(answers),
        output_fn=lambda _l: None,
        sensitive_zone=Zone.FAMILY_PRIVATE,
    )
    assert path.exists()
    profile = store.load("default")
    assert profile.answers["display_name"] == "Sven"
    # Sensitive ref must point at family-private folder.
    assert profile.sensitive_ref is not None
    assert "family-private" in profile.sensitive_ref
    sensitive_path = tmp_path / profile.sensitive_ref
    assert sensitive_path.exists()
    # Main profile must not contain the sensitive answer text.
    text = path.read_text(encoding="utf-8")
    assert "geheim" not in text
