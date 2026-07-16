from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    required_paths = [
        "backend/app/services/document_vector_indexer.py",
        "backend/app/services/document_service.py",
        "backend/app/rag/embedding.py",
        "backend/app/rag/vector_store.py",
    ]
    missing = [path for path in required_paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing document vector indexing paths: {', '.join(missing)}")

    indexer_text = (
        ROOT / "backend" / "app" / "services" / "document_vector_indexer.py"
    ).read_text(encoding="utf-8")
    service_text = (ROOT / "backend" / "app" / "services" / "document_service.py").read_text(
        encoding="utf-8"
    )

    required_fragments = [
        "class DocumentVectorIndexer",
        "class DocumentVectorIndexResult",
        "EmbeddingService",
        "EmbeddingError",
        "QdrantVectorStore",
        "VectorUpsertItem",
        "embed_texts",
        "upsert_chunks",
        "point_id=chunk.id",
        "filename=document.filename",
        "formulas_metadata=chunk.formulas_metadata",
        "skipped=True",
        "persisted_chunks = await self._replace_document_chunks(document, result.chunks)",
        "await DocumentVectorIndexer().index_document_chunks(document, persisted_chunks)",
        "DocumentVectorIndexer().delete_document_vectors(document)",
        "await self.db.flush()",
        "return records",
        "delete_by_document",
    ]
    combined_text = indexer_text + "\n" + service_text
    missing_fragments = [fragment for fragment in required_fragments if fragment not in combined_text]
    if missing_fragments:
        raise SystemExit(
            f"Document vector indexing missing fragments: {', '.join(missing_fragments)}"
        )

    print("Document vector indexing static harness passed.")


if __name__ == "__main__":
    main()
