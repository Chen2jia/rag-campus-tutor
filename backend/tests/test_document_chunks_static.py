from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_document_chunk_model_exists() -> None:
    assert (ROOT / "app" / "models" / "document_chunk.py").exists()


def test_document_chunk_model_stores_rag_metadata() -> None:
    model_text = (ROOT / "app" / "models" / "document_chunk.py").read_text(encoding="utf-8")
    for fragment in [
        "class DocumentChunkRecord",
        '__tablename__ = "document_chunks"',
        "user_id",
        "document_id",
        "chunk_index",
        "page_start",
        "page_end",
        "contains_formula",
        "formulas_metadata",
    ]:
        assert fragment in model_text


def test_document_chunks_are_registered_in_models_and_migrations() -> None:
    init_text = (ROOT / "app" / "models" / "__init__.py").read_text(encoding="utf-8")
    env_text = (ROOT / "alembic" / "env.py").read_text(encoding="utf-8")
    migration_text = (
        ROOT / "alembic" / "versions" / "202607160002_create_document_chunks.py"
    ).read_text(encoding="utf-8")

    assert "DocumentChunkRecord" in init_text
    assert "DocumentChunkRecord" in env_text
    assert "document_chunks" in migration_text
    assert "uq_document_chunks_document_index" in migration_text
    assert "ix_document_chunks_user_id" in migration_text


def test_document_service_persists_processed_chunks() -> None:
    service_text = (ROOT / "app" / "services" / "document_service.py").read_text(encoding="utf-8")
    for fragment in [
        "DocumentChunkRecord",
        "await self._replace_document_chunks(document, result.chunks)",
        "document.total_chunks = result.total_chunks",
        "DocumentChunkRecord.user_id == document.user_id",
        "formulas_metadata=self._serialize_formulas(chunk)",
        '"latex": formula.latex',
    ]:
        assert fragment in service_text
