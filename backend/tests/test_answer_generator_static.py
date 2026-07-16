from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_answer_generator_module_exists() -> None:
    assert (ROOT / "app" / "services" / "answer_generator.py").exists()


def test_answer_generator_has_openai_and_placeholder_paths() -> None:
    service_text = (ROOT / "app" / "services" / "answer_generator.py").read_text(encoding="utf-8")
    for fragment in [
        "class GeneratedAnswer",
        "class AnswerGenerator",
        "RagPromptBuilder",
        "LlmService",
        "LlmServiceError",
        "_openai_is_configured",
        "prompt_builder.build",
        "llm_service.generate",
        "_placeholder_no_context",
        "_placeholder_with_context",
    ]:
        assert fragment in service_text


def test_openai_model_config_is_declared() -> None:
    config_text = (ROOT / "app" / "core" / "config.py").read_text(encoding="utf-8")
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert 'openai_model: str = ""' in config_text
    assert 'openai_base_url: str = ""' in config_text
    assert "OPENAI_MODEL=" in env_text
    assert "OPENAI_BASE_URL=" in env_text
