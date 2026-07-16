from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase10_readme_documents_current_project_status() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for fragment in [
        "Phase 10",
        "用户系统",
        "PDF 处理",
        "混合检索",
        "RAG 问答",
        "Harness",
    ]:
        assert fragment in readme


def test_phase10_readme_documents_runtime_and_model_config() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for fragment in [
        "docker compose up -d",
        "docker compose run --rm migrate",
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "FORMULA_OCR_MIN_CONFIDENCE=0.7",
    ]:
        assert fragment in readme


def test_phase10_readme_documents_harness_and_e2e_flow() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for fragment in [
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "check_e2e_demo_flow.ps1",
        "run_e2e_flow.ps1",
        "EDUMATE_BASE_URL",
        "harness/reports/latest_e2e.json",
        "Target backend does not look like EduMate",
    ]:
        assert fragment in readme
