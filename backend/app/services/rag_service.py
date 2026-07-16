from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.rag import RagAskRequest, RagAskResponse, RagSource
from app.services.answer_generator import AnswerGenerator
from app.services.retrieval_service import RetrievalService
from app.schemas.document import DocumentChunkSearchResult


class RagService:
    def __init__(self, db: AsyncSession) -> None:
        self.retrieval_service = RetrievalService(db)
        self.answer_generator = AnswerGenerator()

    async def ask(self, user: User, payload: RagAskRequest) -> RagAskResponse:
        question = payload.question.strip()
        results = await self.retrieval_service.search(
            user=user,
            query_text=question,
            limit=payload.limit,
            document_id=payload.document_id,
        )
        sources = [
            RagSource(
                document_id=result.document_id,
                filename=result.filename,
                chunk_index=result.chunk_index,
                path=result.path,
                page_start=result.page_start,
                page_end=result.page_end,
                contains_formula=result.contains_formula,
            )
            for result in results
        ]
        context_text = self._format_context(results)
        generated_answer = await self.answer_generator.generate(
            question=question,
            context_text=context_text,
            results=results,
        )
        return RagAskResponse(
            question=question,
            answer=generated_answer.answer,
            sources=sources,
            context_text=context_text,
            is_placeholder=generated_answer.is_placeholder,
            answer_provider=generated_answer.answer_provider,
            model=generated_answer.model,
        )

    @staticmethod
    def _format_context(results: list[DocumentChunkSearchResult]) -> str:
        blocks: list[str] = []
        for index, result in enumerate(results, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"[{index}] {result.filename} / {result.path} / pages {result.page_start}-{result.page_end}",
                        result.text,
                    ]
                )
            )
        return "\n\n".join(blocks)
