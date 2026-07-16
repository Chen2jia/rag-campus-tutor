from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase10_e2e_harness_files_exist() -> None:
    assert (ROOT / "harness" / "runners" / "e2e_demo_flow.py").exists()
    assert (ROOT / "harness" / "scripts" / "check_e2e_demo_flow.ps1").exists()
    assert (ROOT / "harness" / "scripts" / "run_e2e_flow.ps1").exists()


def test_phase10_e2e_harness_matches_plan_flow() -> None:
    runner_text = (ROOT / "harness" / "runners" / "e2e_demo_flow.py").read_text(encoding="utf-8")
    for fragment in [
        "/api/auth/register",
        "/api/auth/login",
        "/api/documents/upload",
        "/api/documents",
        "/api/rag/ask",
        "/api/chat",
        "/api/plan/generate",
        "/api/tasks",
        "assert_backend_matches_project",
        "Target backend does not look like EduMate",
        "document_user_isolation",
        "task_user_isolation",
        "latest_e2e.json",
    ]:
        assert fragment in runner_text


def test_phase10_e2e_harness_checks_sse_events_and_placeholder_safe_rag() -> None:
    runner_text = (ROOT / "harness" / "runners" / "e2e_demo_flow.py").read_text(encoding="utf-8")
    for fragment in [
        "parse_sse_events",
        '"start", "content", "done"',
        "is_placeholder",
        "answer_provider",
        "warnings",
    ]:
        assert fragment in runner_text


def test_phase10_e2e_run_script_starts_stack_and_preflights_backend() -> None:
    script_text = (ROOT / "harness" / "scripts" / "run_e2e_flow.ps1").read_text(encoding="utf-8")
    for fragment in [
        "docker compose up -d postgres qdrant",
        "docker compose run --rm migrate",
        "docker compose up -d backend",
        "Invoke-Checked",
        "SkipDocker",
        "TimeoutSeconds",
        "Wait-EdumateBackend",
        "/api/llm/status",
        "llm_config_check.py",
        "e2e_demo_flow.py",
        "EDUMATE_BASE_URL",
    ]:
        assert fragment in script_text
