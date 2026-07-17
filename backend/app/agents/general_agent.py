from __future__ import annotations

from dataclasses import dataclass

from app.agents.context import AgentContext
from app.services.llm_service import LlmService, LlmServiceError


@dataclass(frozen=True)
class GeneralAgentResponse:
    text: str
    is_placeholder: bool
    answer_provider: str
    model: str | None = None


class GeneralAgent:
    """General conversation agent for non-RAG, non-plan turns."""

    def __init__(self, llm_service: LlmService | None = None) -> None:
        self.llm_service = llm_service or LlmService()

    async def answer(self, context: AgentContext) -> GeneralAgentResponse:
        if not LlmService.is_configured():
            return self._fallback_response(context.message)

        try:
            response = await self.llm_service.generate(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是 EduMate 校园学习助手。请用中文自然对话，回答要简洁、具体、可执行。"
                            "如果用户需要课程资料问答，引导他上传或选择资料；如果用户需要安排学习，"
                            "可以建议生成计划。不要编造已上传资料中不存在的引用。"
                        ),
                    },
                    {"role": "user", "content": context.message},
                ],
                temperature=0.4,
            )
        except LlmServiceError:
            return self._fallback_response(context.message)
        except Exception:
            return self._fallback_response(context.message)

        return GeneralAgentResponse(
            text=response.content,
            is_placeholder=False,
            answer_provider=response.provider,
            model=response.model,
        )

    @staticmethod
    def _fallback_response(message: str) -> GeneralAgentResponse:
        return GeneralAgentResponse(
            text=(
                "我现在可以帮你做三类事情：\n"
                "1. 围绕已上传的课程 PDF 做资料问答和总结。\n"
                "2. 根据目标生成复习计划，并同步创建任务。\n"
                "3. 回答一般学习问题。\n\n"
                f"你刚才说的是：“{message}”。如果你想让我基于资料回答，可以先上传 PDF 或选择资料；"
                "如果你想安排学习，可以直接说“帮我生成 3 天复习计划”。"
            ),
            is_placeholder=True,
            answer_provider="placeholder",
        )
