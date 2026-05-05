from kirobi_core.doctor import (
    PASS,
    check_env_example,
    check_env_file,
    check_makefile,
    render,
    run_doctor,
    summarize,
)


def test_check_env_example_pass(tmp_path):
    (tmp_path / ".env.example").write_text("X=1", encoding="utf-8")
    assert check_env_example(tmp_path).status == PASS


def test_check_env_file_warns_when_missing(tmp_path):
    assert check_env_file(tmp_path).status == "warn"


def test_check_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("all:", encoding="utf-8")
    assert check_makefile(tmp_path).status == PASS


def test_run_doctor_returns_results_for_each_check(tmp_path):
    (tmp_path / ".env.example").write_text("", encoding="utf-8")
    (tmp_path / "Makefile").write_text("", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services: {}", encoding="utf-8")
    results = run_doctor(tmp_path)
    assert len(results) >= 5
    p, w, f = summarize(results)
    assert p + w + f == len(results)
    text = render(results)
    assert "Summary:" in text
