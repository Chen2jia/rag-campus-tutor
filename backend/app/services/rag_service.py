from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.document import DocumentChunkSearchResult
from app.schemas.rag import RagAskRequest, RagAskResponse, RagSource
from app.services.document_service import DocumentService


class RagService:
    def __init__(self, db: AsyncSession) -> None:
        self.document_service = DocumentService(db)

    async def ask(self, user: User, payload: RagAskRequest) -> RagAskResponse:
        question = payload.question.strip()
        search_response = await self.document_service.search_chunks(
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
            for result in search_response.results
        ]
        context_text = self._format_context(search_response.results)
        return RagAskResponse(
            question=question,
            answer=self._build_placeholder_answer(question=question, sources=sources),
            sources=sources,
            context_text=context_text,
            is_placeholder=True,
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

    @staticmethod
    def _build_placeholder_answer(question: str, sources: list[RagSource]) -> str:
        if not sources:
            return (
                f"暂时没有在已上传资料中找到和「{question}」直接相关的内容。"
                "后续接入向量检索和大模型后，可以给出更完整的解释。"
            )
        source_count = len(sources)
        return (
            f"已从已上传资料中找到 {source_count} 个相关片段。"
            "当前是占位回答，下一步会接入大模型，根据 sources 和 context_text 生成正式答案。"
        )
