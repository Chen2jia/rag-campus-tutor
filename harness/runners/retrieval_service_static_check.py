from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/services/retrieval_service.py",
        "backend/app/services/rag_service.py",
        "backend/app/rag/embedding.py",
        "backend/app/rag/vector_store.py",
        "backend/app/rag/bm25_store.py",
        "backend/app/rag/retriever.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing retrieval service paths: {', '.join(missing)}")

    retrieval_text = (
        ROOT / "backend" / "app" / "services" / "retrieval_service.py"
    ).read_text(encoding="utf-8")
    rag_text = (ROOT / "backend" / "app" / "services" / "rag_service.py").read_text(
        encoding="utf-8"
    )

    required_fragments = [
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
        "DocumentChunkRecord.user_id == user.id",
        "Document.user_id == user.id",
        "DocumentChunkRecord.document_id == document_id",
        "except EmbeddingError",
        "RetrievalService(db)",
        "retrieval_service.search",
        "context_text = self._format_context(results)",
    ]
    combined_text = retrieval_text + "\n" + rag_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(f"Retrieval service missing fragments: {', '.join(missing_fragments)}")

    print("Retrieval service static harness passed.")


if __name__ == "__main__":
    main()
