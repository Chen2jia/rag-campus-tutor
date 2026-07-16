from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[0]


def test_llm_config_status_endpoint_exists_and_is_safe() -> None:
    router_text = (ROOT / "app" / "routers" / "health.py").read_text(encoding="utf-8")
    for fragment in [
        '@router.get("/llm/status")',
        "LlmService.config_status()",
        '"configured"',
        '"provider"',
        '"model"',
        '"base_url_host"',
        '"missing"',
        '"placeholder"',
    ]:
        assert fragment in router_text
    assert "openai_api_key" not in router_text
    assert "OPENAI_API_KEY" not in router_text


def test_llm_service_exposes_redacted_config_status() -> None:
    service_text = (ROOT / "app" / "services" / "llm_service.py").read_text(encoding="utf-8")
    for fragment in [
        "class LlmConfigStatus",
        "configured: bool",
        "base_url_host: str | None",
        "missing: list[str]",
        "def config_status",
        'missing.append("OPENAI_API_KEY")',
        'missing.append("OPENAI_MODEL")',
        "def _base_url_host",
        "urlparse(base_url)",
    ]:
        assert fragment in service_text


def test_llm_config_harness_exists_and_checks_secret_leaks() -> None:
    runner = PROJECT_ROOT / "harness" / "runners" / "llm_config_check.py"
    script = PROJECT_ROOT / "harness" / "scripts" / "check_llm_config.ps1"
    assert runner.exists()
    assert script.exists()

    runner_text = runner.read_text(encoding="utf-8")
    for fragment in [
        "/api/llm/status",
        "assert_no_secret_leak",
        "api_key",
        "sk-",
        "latest_llm_config.json",
        "EDUMATE_BASE_URL",
        "Cannot reach EduMate backend",
        "Target backend does not expose EduMate /api/llm/status",
    ]:
        assert fragment in runner_text
