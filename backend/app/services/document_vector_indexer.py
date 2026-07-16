from __future__ import annotations

import logging
from dataclasses import dataclass

from app.models.document import Document
from app.models.document_chunk import DocumentChunkRecord
from app.rag.embedding import EmbeddingError, EmbeddingService
from app.rag.vector_store import QdrantVectorStore, VectorUpsertItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentVectorIndexResult:
    indexed_chunks: int
    skipped: bool = False
    error_message: str | None = None


class DocumentVectorIndexer:
    """Indexes persisted document chunks into the vector store."""

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or QdrantVectorStore()

    async def index_document_chunks(
        self,
        document: Document,
        chunks: list[DocumentChunkRecord],
    ) -> DocumentVectorIndexResult:
        if not chunks:
            return DocumentVectorIndexResult(indexed_chunks=0, skipped=True)

        try:
            embeddings = await self.embedding_service.embed_texts([chunk.text for chunk in chunks])
        except EmbeddingError as exc:
            logger.info("Skipping vector indexing for document %s: %s", document.id, exc)
            return DocumentVectorIndexResult(indexed_chunks=0, skipped=True, error_message=str(exc))

        items = [
            VectorUpsertItem(
                point_id=chunk.id,
                user_id=chunk.user_id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                filename=document.filename,
                text=chunk.text,
                path=chunk.path,
                section=chunk.section,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                contains_formula=chunk.contains_formula,
                formulas_metadata=chunk.formulas_metadata,
                vector=embedding.vector,
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

        try:
            self.vector_store.upsert_chunks(items)
        except Exception as exc:  # pragma: no cover - vector infra is optional during upload
            logger.warning("Skipping vector indexing for document %s: %s", document.id, exc)
            return DocumentVectorIndexResult(indexed_chunks=0, skipped=True, error_message=str(exc))

        return DocumentVectorIndexResult(indexed_chunks=len(items))

    def delete_document_vectors(self, document: Document) -> None:
        try:
            self.vector_store.delete_by_document(user_id=document.user_id, document_id=document.id)
        except Exception as exc:  # pragma: no cover - best-effort cleanup
            logger.warning("Failed to delete vectors for document %s: %s", document.id, exc)
