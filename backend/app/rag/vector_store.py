from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any
from uuid import UUID

from app.core.config import settings

DEFAULT_COLLECTION_NAME = "knowledge_chunks"


@dataclass(frozen=True)
class VectorUpsertItem:
    point_id: UUID
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
    formulas_metadata: list[dict[str, object]]
    vector: list[float]


@dataclass(frozen=True)
class VectorSearchHit:
    point_id: str
    score: float
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


class VectorStoreError(RuntimeError):
    pass


class QdrantVectorStore:
    """Lightweight Qdrant wrapper for knowledge chunk storage and search."""

    def __init__(
        self,
        collection_name: str | None = None,
        vector_size: int | None = None,
        qdrant_url: str | None = None,
    ) -> None:
        self.collection_name = collection_name or settings.qdrant_collection_name or DEFAULT_COLLECTION_NAME
        self.vector_size = vector_size or settings.embedding_dimension
        self.qdrant_url = qdrant_url or settings.qdrant_url

    def ensure_collection(self) -> None:
        client = self._build_client()
        models = self._models_module()
        try:
            client.get_collection(self.collection_name)
        except Exception:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    def upsert_chunks(self, items: list[VectorUpsertItem]) -> None:
        if not items:
            return

        client = self._build_client()
        models = self._models_module()
        self.ensure_collection()
        client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(item.point_id),
                    vector=item.vector,
                    payload=self._build_payload(item),
                )
                for item in items
            ],
        )

    def search_chunks(
        self,
        user_id: UUID,
        query_vector: list[float],
        limit: int = 10,
        document_id: UUID | None = None,
    ) -> list[VectorSearchHit]:
        client = self._build_client()
        models = self._models_module()
        self.ensure_collection()
        search_filter = self._build_filter(user_id=user_id, document_id=document_id, models=models)
        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return [self._to_hit(result) for result in results]

    def delete_by_user(self, user_id: UUID) -> None:
        self._delete_by_filter(self._build_filter(user_id=user_id, document_id=None, models=self._models_module()))

    def delete_by_document(self, user_id: UUID, document_id: UUID) -> None:
        self._delete_by_filter(
            self._build_filter(user_id=user_id, document_id=document_id, models=self._models_module())
        )

    def _delete_by_filter(self, filter_: Any) -> None:
        client = self._build_client()
        models = self._models_module()
        self.ensure_collection()
        client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=filter_),
        )

    def _build_client(self) -> Any:
        qdrant_module = import_module("qdrant_client")
        return qdrant_module.QdrantClient(url=self.qdrant_url)

    @staticmethod
    def _models_module() -> Any:
        return import_module("qdrant_client.http.models")

    @staticmethod
    def _build_payload(item: VectorUpsertItem) -> dict[str, Any]:
        return {
            "point_id": str(item.point_id),
            "user_id": str(item.user_id),
            "document_id": str(item.document_id),
            "chunk_index": item.chunk_index,
            "filename": item.filename,
            "text": item.text,
            "path": item.path,
            "section": item.section,
            "page_start": item.page_start,
            "page_end": item.page_end,
            "contains_formula": item.contains_formula,
            "formulas_metadata": item.formulas_metadata,
        }

    @staticmethod
    def _build_filter(user_id: UUID, document_id: UUID | None, models: Any) -> Any:
        must = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user_id))),
        ]
        if document_id is not None:
            must.append(models.FieldCondition(key="document_id", match=models.MatchValue(value=str(document_id))))
        return models.Filter(must=must)

    @staticmethod
    def _to_hit(result: Any) -> VectorSearchHit:
        payload = getattr(result, "payload", {}) or {}
        return VectorSearchHit(
            point_id=str(getattr(result, "id", "")),
            score=float(getattr(result, "score", 0.0)),
            user_id=UUID(str(payload.get("user_id"))),
            document_id=UUID(str(payload.get("document_id"))),
            chunk_index=int(payload.get("chunk_index", 0)),
            filename=str(payload.get("filename", "")),
            text=str(payload.get("text", "")),
            path=str(payload.get("path", "")),
            section=str(payload.get("section", "")),
            page_start=int(payload.get("page_start", 0)),
            page_end=int(payload.get("page_end", 0)),
            contains_formula=bool(payload.get("contains_formula", False)),
        )
