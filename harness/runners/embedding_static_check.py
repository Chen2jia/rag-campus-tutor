from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/rag/embedding.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing embedding paths: {', '.join(missing)}")

    embedding_text = (ROOT / "backend" / "app" / "rag" / "embedding.py").read_text(
        encoding="utf-8"
    )
    config_text = (ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    env_text = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")
    requirements_text = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")

    required_fragments = [
        "class EmbeddingService",
        "EmbeddingResult",
        "EmbeddingError",
        "max_retries",
        "text-embedding-3-small",
        "client.embeddings.create",
        'import_module("openai")',
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "openai==1.59.7",
    ]
    combined_text = "\n".join([embedding_text, config_text, env_text, requirements_text])
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Embedding module missing fragments: {', '.join(missing_fragments)}")

    print("Embedding static harness passed.")


if __name__ == "__main__":
    main()
