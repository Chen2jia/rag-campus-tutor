from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase10_e2e_harness_files_exist() -> None:
    assert (ROOT / "harness" / "runners" / "e2e_demo_flow.py").exists()
    assert (ROOT / "harness" / "scripts" / "check_e2e_demo_flow.ps1").exists()


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
