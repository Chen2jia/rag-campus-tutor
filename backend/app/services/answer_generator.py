from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any

from app.core.config import settings
from app.schemas.document import DocumentChunkSearchResult


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    is_placeholder: bool
    answer_provider: str
    model: str | None = None


class AnswerGenerator:
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
            answer = await self._generate_with_openai(question=question, context_text=context_text)
        except Exception:
            return self._placeholder_with_context(question=question, results=results)

        return GeneratedAnswer(
            answer=answer,
            is_placeholder=False,
            answer_provider="openai",
            model=settings.openai_model,
        )

    @staticmethod
    def _openai_is_configured() -> bool:
        api_key = settings.openai_api_key.strip()
        model = settings.openai_model.strip()
        return bool(api_key and model and api_key not in {"sk-change-me", "change-me"})

    async def _generate_with_openai(self, question: str, context_text: str) -> str:
        openai_module = import_module("openai")
        client = openai_module.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 EduMate 校园学习助手。只根据给定资料回答；"
                        "如果资料不足，明确说明不知道。保留公式的标准 LaTeX，"
                        "并用 [1]、[2] 这样的编号引用来源。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"问题：{question}\n\n资料：\n{context_text}",
                },
            ],
            temperature=0.2,
        )
        return self._extract_message_text(response)

    @staticmethod
    def _extract_message_text(response: Any) -> str:
        content = response.choices[0].message.content
        if isinstance(content, str) and content.strip():
            return content.strip()
        return "模型没有返回有效文本，请稍后重试。"

    @staticmethod
    def _placeholder_no_context(question: str) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer=(
                f"暂时没有在已上传资料中找到和「{question}」直接相关的内容。"
                "后续接入向量检索和大模型后，可以给出更完整的解释。"
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
                f"已从已上传资料中找到 {len(results)} 个和「{question}」相关的片段。"
                "当前未启用真实模型生成，因此先返回检索上下文；配置 OPENAI_API_KEY 和 OPENAI_MODEL 后可生成正式答案。"
            ),
            is_placeholder=True,
            answer_provider="placeholder",
        )
