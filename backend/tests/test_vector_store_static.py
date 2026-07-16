from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vector_store_module_exists() -> None:
    assert (ROOT / "app" / "rag" / "vector_store.py").exists()


def test_vector_store_uses_qdrant_collection_and_filter_ops() -> None:
    vector_text = (ROOT / "app" / "rag" / "vector_store.py").read_text(encoding="utf-8")
    for fragment in [
        "class VectorUpsertItem",
        "class VectorSearchHit",
        "class QdrantVectorStore",
        "knowledge_chunks",
        "embedding_dimension",
        "VectorParams",
        "Distance.COSINE",
        "PointStruct",
        "create_collection",
        "upsert(",
        "search(",
        "query_filter",
        "delete(",
        "FilterSelector",
        "_build_payload",
        "_build_filter",
        "_to_hit",
    ]:
        assert fragment in vector_text


def test_vector_store_exposes_user_scoped_delete_paths() -> None:
    vector_text = (ROOT / "app" / "rag" / "vector_store.py").read_text(encoding="utf-8")
    assert "delete_by_user" in vector_text
    assert "delete_by_document" in vector_text
    assert 'key="user_id"' in vector_text
    assert 'key="document_id"' in vector_text
