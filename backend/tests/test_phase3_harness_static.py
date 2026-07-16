from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase3_static_harness_exists() -> None:
    script = ROOT / "harness" / "scripts" / "check_phase3_static.ps1"
    assert script.exists()


def test_phase3_static_harness_runs_all_static_checks() -> None:
    script_text = (ROOT / "harness" / "scripts" / "check_phase3_static.ps1").read_text(
        encoding="utf-8"
    )
    for check_script in [
        "check_skeleton.ps1",
        "check_auth_static.ps1",
        "check_documents_static.ps1",
        "check_tasks_static.ps1",
        "check_review_static.ps1",
        "check_plan_static.ps1",
    ]:
        assert check_script in script_text


def test_harness_readme_mentions_phase3_static_gate() -> None:
    readme = (ROOT / "harness" / "README.md").read_text(encoding="utf-8")
    assert "check_phase3_static.ps1" in readme
    assert "does not require Docker" in readme
