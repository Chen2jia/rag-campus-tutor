from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prompt_builder_and_llm_service_modules_exist() -> None:
    assert (ROOT / "app" / "rag" / "prompt_builder.py").exists()
    assert (ROOT / "app" / "services" / "llm_service.py").exists()


def test_prompt_builder_preserves_grounding_citation_and_latex_rules() -> None:
    prompt_text = (ROOT / "app" / "rag" / "prompt_builder.py").read_text(encoding="utf-8")
    for fragment in [
        "class RagPrompt",
        "class RagPromptBuilder",
        "只根据给定资料回答",
        "资料不足",
        "LaTeX",
        "[1]、[2]",
        "问题：{question}",
        "资料：",
    ]:
        assert fragment in prompt_text


def test_llm_service_supports_openai_compatible_base_url() -> None:
    service_text = (ROOT / "app" / "services" / "llm_service.py").read_text(encoding="utf-8")
    for fragment in [
        "class LlmResponse",
        "class LlmConfigStatus",
        "class LlmServiceError",
        "class LlmService",
        'import_module("openai")',
        "AsyncOpenAI",
        "client.chat.completions.create",
        "settings.openai_base_url",
        'client_kwargs["base_url"]',
        "_provider_name",
        "deepseek",
        "openai-compatible",
        "is_configured",
        "config_status",
        "_base_url_host",
    ]:
        assert fragment in service_text


def test_llm_config_declares_base_url_for_deepseek_compatible_mode() -> None:
    config_text = (ROOT / "app" / "core" / "config.py").read_text(encoding="utf-8")
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert 'openai_base_url: str = ""' in config_text
    assert "OPENAI_BASE_URL=" in env_text
