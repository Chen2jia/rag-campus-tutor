from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/rag/prompt_builder.py",
        "backend/app/services/llm_service.py",
        "backend/app/services/answer_generator.py",
        "backend/app/core/config.py",
        "backend/.env.example",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing LLM service paths: {', '.join(missing)}")

    prompt_text = (ROOT / "backend" / "app" / "rag" / "prompt_builder.py").read_text(
        encoding="utf-8"
    )
    service_text = (ROOT / "backend" / "app" / "services" / "llm_service.py").read_text(
        encoding="utf-8"
    )
    generator_text = (
        ROOT / "backend" / "app" / "services" / "answer_generator.py"
    ).read_text(encoding="utf-8")
    config_text = (ROOT / "backend" / "app" / "core" / "config.py").read_text(
        encoding="utf-8"
    )
    env_text = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")

    required_fragments = [
        "class RagPromptBuilder",
        "只根据给定资料回答",
        "LaTeX",
        "class LlmService",
        "class LlmServiceError",
        'import_module("openai")',
        "AsyncOpenAI",
        "client.chat.completions.create",
        "settings.openai_base_url",
        'client_kwargs["base_url"]',
        "deepseek",
        "openai-compatible",
        "RagPromptBuilder",
        "LlmService",
        "LlmServiceError",
        "prompt_builder.build",
        "llm_service.generate",
        'openai_base_url: str = ""',
        "OPENAI_BASE_URL=",
    ]
    combined_text = "\n".join([prompt_text, service_text, generator_text, config_text, env_text])
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"LLM service missing fragments: {', '.join(missing_fragments)}")

    print("LLM service static harness passed.")


if __name__ == "__main__":
    main()
