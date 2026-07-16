from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from app.rag.bm25_store import Bm25Hit
from app.rag.vector_store import VectorSearchHit


@dataclass(frozen=True)
class HybridSearchHit:
    key: str
    score: float
    source_scores: dict[str, float]
    user_id: UUID
    document_id: UUID
    chunk_index: int
    filename: str
    text: str
    path: str
    section: str
    page_start: int
    page_end: int
    contains_formula: bool


class HybridRetriever:
    """RRF fusion helper for semantic and keyword retrieval results."""

    def __init__(self, rrf_k: int = 60) -> None:
        self.rrf_k = rrf_k

    def fuse(
        self,
        vector_hits: list[VectorSearchHit],
        bm25_hits: list[Bm25Hit],
        limit: int = 5,
    ) -> list[HybridSearchHit]:
        ranked: dict[str, HybridSearchHit] = {}
        self._accumulate(ranked, vector_hits, source_name="vector")
        self._accumulate(ranked, bm25_hits, source_name="bm25")
        return sorted(ranked.values(), key=lambda item: item.score, reverse=True)[:limit]

    def score_hits(
        self,
        vector_hits: list[VectorSearchHit],
        bm25_hits: list[Bm25Hit],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        self._accumulate_scores(scores, vector_hits)
        self._accumulate_scores(scores, bm25_hits)
        return scores

    @staticmethod
    def build_key(user_id: UUID, document_id: UUID, chunk_index: int) -> str:
        return f"{user_id}:{document_id}:{chunk_index}"

    def _accumulate(
        self,
        ranked: dict[str, HybridSearchHit],
        hits: Iterable[VectorSearchHit | Bm25Hit],
        source_name: str,
    ) -> None:
        for position, hit in enumerate(hits, start=1):
            key = self._hit_key(hit)
            contribution = self._rrf_score(position)
            if key not in ranked:
                ranked[key] = self._build_hybrid_hit(hit=hit, score=contribution, source_name=source_name)
                continue
            existing = ranked[key]
            ranked[key] = HybridSearchHit(
                key=existing.key,
                score=existing.score + contribution,
                source_scores={**existing.source_scores, source_name: contribution},
                user_id=existing.user_id,
                document_id=existing.document_id,
                chunk_index=existing.chunk_index,
                filename=existing.filename,
                text=existing.text,
                path=existing.path,
                section=existing.section,
                page_start=existing.page_start,
                page_end=existing.page_end,
                contains_formula=existing.contains_formula,
            )

    def _accumulate_scores(
        self,
        scores: dict[str, float],
        hits: Iterable[VectorSearchHit | Bm25Hit],
    ) -> None:
        for position, hit in enumerate(hits, start=1):
            key = self._hit_key(hit)
            scores[key] = scores.get(key, 0.0) + self._rrf_score(position)

    def _build_hybrid_hit(
        self,
        hit: VectorSearchHit | Bm25Hit,
        score: float,
        source_name: str,
    ) -> HybridSearchHit:
        if isinstance(hit, VectorSearchHit):
            user_id = hit.user_id
            document_id = hit.document_id
            chunk_index = hit.chunk_index
            filename = hit.filename
            text = hit.text
            path = hit.path
            section = hit.section
            page_start = hit.page_start
            page_end = hit.page_end
            contains_formula = hit.contains_formula
        else:
            user_id, document_id, chunk_index = self._split_key(hit.key)
            filename = ""
            text = hit.text
            path = ""
            section = ""
            page_start = 0
            page_end = 0
            contains_formula = False

        return HybridSearchHit(
            key=self._hit_key(hit),
            score=score,
            source_scores={source_name: score},
            user_id=user_id,
            document_id=document_id,
            chunk_index=chunk_index,
            filename=filename,
            text=text,
            path=path,
            section=section,
            page_start=page_start,
            page_end=page_end,
            contains_formula=contains_formula,
        )

    @staticmethod
    def _hit_key(hit: VectorSearchHit | Bm25Hit) -> str:
        if isinstance(hit, VectorSearchHit):
            return HybridRetriever.build_key(hit.user_id, hit.document_id, hit.chunk_index)
        return hit.key

    def _rrf_score(self, rank: int) -> float:
        return 1.0 / (self.rrf_k + rank)

    @staticmethod
    def _split_key(key: str) -> tuple[UUID, UUID, int]:
        user_id, document_id, chunk_index = key.split(":", 2)
        return UUID(user_id), UUID(document_id), int(chunk_index)
