from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_llm_live_smoke_files_exist() -> None:
    assert (ROOT / "backend" / "scripts" / "llm_live_smoke.py").exists()
    assert (ROOT / "harness" / "scripts" / "run_llm_live_smoke.ps1").exists()


def test_llm_live_smoke_does_not_print_or_report_secrets() -> None:
    smoke_text = (ROOT / "backend" / "scripts" / "llm_live_smoke.py").read_text(encoding="utf-8")
    for fragment in [
        "redact",
        "safe_error",
        "sk-***",
        "latest_llm_live_smoke.json",
        "Path.cwd().name.lower() == \"backend\"",
        "response_preview",
        "sys.path.insert",
        "LlmService",
        "service.generate",
    ]:
        assert fragment in smoke_text
    assert "openai_api_key" not in smoke_text
    assert "OPENAI_API_KEY" not in smoke_text


def test_llm_live_smoke_runner_uses_docker_backend_by_default() -> None:
    script_text = (ROOT / "harness" / "scripts" / "run_llm_live_smoke.ps1").read_text(
        encoding="utf-8"
    )
    for fragment in [
        "backend/.env",
        "--volume ./harness/reports:/app/harness/reports",
        "backend python scripts/llm_live_smoke.py",
        "$Local",
        "OPENAI_API_KEY / OPENAI_MODEL",
    ]:
        assert fragment in script_text


def test_backend_dockerfile_copies_scripts_for_live_smoke() -> None:
    dockerfile = (ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY scripts ./scripts" in dockerfile
