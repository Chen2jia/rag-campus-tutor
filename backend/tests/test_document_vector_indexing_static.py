from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_document_vector_indexer_module_exists() -> None:
    assert (ROOT / "app" / "services" / "document_vector_indexer.py").exists()


def test_document_vector_indexer_embeds_and_upserts_persisted_chunks() -> None:
    indexer_text = (ROOT / "app" / "services" / "document_vector_indexer.py").read_text(
        encoding="utf-8"
    )
    for fragment in [
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
        "strict=True",
        "skipped=True",
    ]:
        assert fragment in indexer_text


def test_document_service_indexes_after_chunk_persistence() -> None:
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    for fragment in [
        "DocumentVectorIndexer",
        "persisted_chunks = await self._replace_document_chunks(document, result.chunks)",
        "await DocumentVectorIndexer().index_document_chunks(document, persisted_chunks)",
        "DocumentVectorIndexer().delete_document_vectors(document)",
        "await self.db.flush()",
        "return records",
    ]:
        assert fragment in service_text


def test_document_vector_cleanup_is_best_effort() -> None:
    indexer_text = (ROOT / "app" / "services" / "document_vector_indexer.py").read_text(
        encoding="utf-8"
    )
    assert "delete_document_vectors" in indexer_text
    assert "delete_by_document" in indexer_text
    assert "best-effort cleanup" in indexer_text
