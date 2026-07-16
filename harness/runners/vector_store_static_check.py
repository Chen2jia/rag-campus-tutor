from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/rag/vector_store.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing vector store paths: {', '.join(missing)}")

    vector_text = (ROOT / "backend" / "app" / "rag" / "vector_store.py").read_text(
        encoding="utf-8"
    )
    config_text = (ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    env_text = (ROOT / "backend" / ".env.example").read_text(encoding="utf-8")

    required_fragments = [
        "class VectorUpsertItem",
        "class VectorSearchHit",
        "class QdrantVectorStore",
        "knowledge_chunks",
        "embedding_dimension",
        "ensure_collection",
        "create_collection",
        "upsert(",
        "search(",
        "delete(",
        "delete_by_user",
        "delete_by_document",
        "FilterSelector",
        "VectorParams",
        "Distance.COSINE",
        "PointStruct",
        "query_filter",
        'qdrant_collection_name: str = "knowledge_chunks"',
    ]
    combined_text = "\n".join([vector_text, config_text, env_text])
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Vector store missing fragments: {', '.join(missing_fragments)}")

    print("Vector store static harness passed.")


if __name__ == "__main__":
    main()
