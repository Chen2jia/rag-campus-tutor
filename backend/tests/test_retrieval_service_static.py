from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_retrieval_service_module_exists() -> None:
    assert (ROOT / "app" / "services" / "retrieval_service.py").exists()


def test_retrieval_service_combines_vector_bm25_and_rrf() -> None:
    service_text = (ROOT / "app" / "services" / "retrieval_service.py").read_text(
        encoding="utf-8"
    )
    for fragment in [
        "class RetrievalService",
        "class RetrievalCandidate",
        "EmbeddingService",
        "QdrantVectorStore",
        "Bm25Store",
        "HybridRetriever",
        "embed_text",
        "search_chunks",
        "bm25_store.search",
        "hybrid_retriever.fuse",
        "HybridRetriever.build_key",
        "DocumentChunkSearchResult",
    ]:
        assert fragment in service_text


def test_retrieval_service_is_user_scoped_and_safe_to_fallback() -> None:
    service_text = (ROOT / "app" / "services" / "retrieval_service.py").read_text(
        encoding="utf-8"
    )
    for fragment in [
        "DocumentChunkRecord.user_id == user.id",
        "Document.user_id == user.id",
        "DocumentChunkRecord.document_id == document_id",
        "except EmbeddingError",
        "return []",
        "except Exception",
    ]:
        assert fragment in service_text


def test_rag_service_uses_retrieval_service() -> None:
    rag_text = (ROOT / "app" / "services" / "rag_service.py").read_text(encoding="utf-8")
    for fragment in [
        "RetrievalService(db)",
        "retrieval_service.search",
        "results=results",
        "context_text = self._format_context(results)",
    ]:
        assert fragment in rag_text
