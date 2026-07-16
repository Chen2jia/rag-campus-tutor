from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_embedding_module_exists() -> None:
    assert (ROOT / "app" / "rag" / "embedding.py").exists()


def test_embedding_service_has_retry_and_lazy_openai_paths() -> None:
    embedding_text = (ROOT / "app" / "rag" / "embedding.py").read_text(encoding="utf-8")
    for fragment in [
        "class EmbeddingResult",
        "class EmbeddingError",
        "class EmbeddingService",
        "embed_text",
        "embed_texts",
        "max_retries",
        "_normalize_text",
        "_build_client",
        'import_module("openai")',
        "AsyncOpenAI",
        "client.embeddings.create",
        "_extract_vector",
    ]:
        assert fragment in embedding_text


def test_embedding_service_rejects_empty_text() -> None:
    embedding_text = (ROOT / "app" / "rag" / "embedding.py").read_text(encoding="utf-8")
    assert "Cannot embed empty text" in embedding_text
    assert "OPENAI_API_KEY is not configured" in embedding_text
    config_text = (ROOT / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert 'embedding_model: str = "text-embedding-3-small"' in config_text
