from __future__ import annotations

import json
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.chat import ChatRequest
from app.schemas.rag import RagAskRequest, RagAskResponse
from app.services.rag_service import RagService


class KnowledgeAgent:
    """Knowledge QA agent that streams RAG answers as SSE events."""

    def __init__(self, db: AsyncSession) -> None:
        self.rag_service = RagService(db)

    async def answer(self, user: User, payload: ChatRequest) -> RagAskResponse:
        return await self.rag_service.ask(
            user=user,
            payload=RagAskRequest(
                question=payload.message,
                limit=payload.limit,
                document_id=payload.document_id,
            ),
        )

    async def stream_answer(self, user: User, payload: ChatRequest) -> AsyncIterator[str]:
        yield self._sse("start", {"message": payload.message})
        try:
            response = await self.answer(user=user, payload=payload)
            if response.answer:
                yield self._sse(
                    "content", {
                        "text": response.answer,
                        "is_placeholder": response.is_placeholder,
                        "answer_provider": response.answer_provider,
                        "model": response.model,
                    },
                )
            yield self._sse(
                "citations", {
                    "sources": [source.model_dump(mode="json") for source in response.sources],
                    "context_text": response.context_text,
                },
            )
            yield self._sse("done", {"source_count": len(response.sources)})
        except Exception as exc:
            yield self._sse("error", {"message": str(exc)})

    @staticmethod
    def _sse(event: str, data: dict[str, object]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
