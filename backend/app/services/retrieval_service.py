from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunkRecord
from app.models.user import User
from app.rag.bm25_store import Bm25Store
from app.rag.embedding import EmbeddingError, EmbeddingService
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import QdrantVectorStore, VectorSearchHit
from app.schemas.document import DocumentChunkSearchResult


@dataclass(frozen=True)
class RetrievalCandidate:
    key: str
    result: DocumentChunkSearchResult


class RetrievalService:
    """User-scoped hybrid retrieval over persisted chunks and vector index."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        vector_store: QdrantVectorStore | None = None,
        bm25_store: Bm25Store | None = None,
        hybrid_retriever: HybridRetriever | None = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or QdrantVectorStore()
        self.bm25_store = bm25_store or Bm25Store()
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()

    async def search(
        self,
        user: User,
        query_text: str,
        limit: int = 5,
        document_id: UUID | None = None,
    ) -> list[DocumentChunkSearchResult]:
        clean_query = query_text.strip()
        if not clean_query:
            return []

        candidates = await self._load_candidates(user=user, document_id=document_id)
        candidate_map = {candidate.key: candidate.result for candidate in candidates}
        bm25_hits = self.bm25_store.search(
            query=clean_query,
            documents=[(candidate.key, candidate.result.text) for candidate in candidates],
            limit=max(limit * 2, 10),
        )
        vector_hits = await self._search_vectors(
            user_id=user.id,
            query_text=clean_query,
            limit=max(limit * 2, 10),
            document_id=document_id,
        )
        fused_hits = self.hybrid_retriever.fuse(
            vector_hits=vector_hits,
            bm25_hits=bm25_hits,
            limit=limit,
        )
        return [
            candidate_map[hit.key]
            for hit in fused_hits
            if hit.key in candidate_map
        ]

    async def _load_candidates(
        self,
        user: User,
        document_id: UUID | None,
    ) -> list[RetrievalCandidate]:
        statement = (
            select(DocumentChunkRecord, Document.filename)
            .join(Document, Document.id == DocumentChunkRecord.document_id)
            .where(
                DocumentChunkRecord.user_id == user.id,
                Document.user_id == user.id,
            )
            .order_by(Document.created_at.desc(), DocumentChunkRecord.chunk_index.asc())
        )
        if document_id is not None:
            statement = statement.where(DocumentChunkRecord.document_id == document_id)

        rows = (await self.db.execute(statement)).all()
        return [
            RetrievalCandidate(
                key=HybridRetriever.build_key(
                    user_id=chunk.user_id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                ),
                result=DocumentChunkSearchResult(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    filename=filename,
                    chunk_index=chunk.chunk_index,
                    path=chunk.path,
                    section=chunk.section,
                    text=chunk.text,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    contains_formula=chunk.contains_formula,
                    formulas_metadata=chunk.formulas_metadata,
                ),
            )
            for chunk, filename in rows
        ]

    async def _search_vectors(
        self,
        user_id: UUID,
        query_text: str,
        limit: int,
        document_id: UUID | None,
    ) -> list[VectorSearchHit]:
        try:
            embedding = await self.embedding_service.embed_text(query_text)
            return self.vector_store.search_chunks(
                user_id=user_id,
                query_vector=embedding.vector,
                limit=limit,
                document_id=document_id,
            )
        except EmbeddingError:
            return []
        except Exception:
            return []
