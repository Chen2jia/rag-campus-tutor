from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.rag.prompt_builder import RagPromptBuilder
from app.schemas.document import DocumentChunkSearchResult
from app.services.llm_service import LlmService, LlmServiceError


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    is_placeholder: bool
    answer_provider: str
    model: str | None = None


class AnswerGenerator:
    def __init__(
        self,
        prompt_builder: RagPromptBuilder | None = None,
        llm_service: LlmService | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or RagPromptBuilder()
        self.llm_service = llm_service or LlmService()

    async def generate(
        self,
        question: str,
        context_text: str,
        results: list[DocumentChunkSearchResult],
    ) -> GeneratedAnswer:
        if not results:
            return self._placeholder_no_context(question)
        if not self._openai_is_configured():
            return self._placeholder_with_context(question=question, results=results)

        try:
            prompt = self.prompt_builder.build(question=question, context_text=context_text)
            response = await self.llm_service.generate(messages=prompt.messages, temperature=0.2)
        except LlmServiceError:
            return self._placeholder_with_context(question=question, results=results)
        except Exception:
            return self._placeholder_with_context(question=question, results=results)

        return GeneratedAnswer(
            answer=response.content,
            is_placeholder=False,
            answer_provider=response.provider,
            model=response.model,
        )

    @staticmethod
    def _openai_is_configured() -> bool:
        return LlmService.is_configured()

    @staticmethod
    def _placeholder_no_context(question: str) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer=(
                f"我暂时没有在已上传资料中找到和“{question}”直接相关的内容。\n\n"
                "你可以换一种问法，或者先上传更相关的课程 PDF。如果这是普通学习问题，"
                "也可以直接在聊天页提问，我会按通用学习助手的方式回答。"
            ),
            is_placeholder=True,
            answer_provider="placeholder",
        )

    @staticmethod
    def _placeholder_with_context(
        question: str,
        results: list[DocumentChunkSearchResult],
    ) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer=(
                f"我已经从已上传资料中找到 {len(results)} 个和“{question}”相关的片段。\n\n"
                "当前运行中的后端还没有启用真实模型生成，所以先返回检索上下文。"
                "配置 OPENAI_API_KEY 和 OPENAI_MODEL 后，会生成正式答案；使用 DeepSeek 时，"
                "请同时配置 OPENAI_BASE_URL。"
            ),
            is_placeholder=True,
            answer_provider="placeholder",
            model=settings.openai_model or None,
        )
