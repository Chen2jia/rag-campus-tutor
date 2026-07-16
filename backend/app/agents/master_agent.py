from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.planner_agent import PlannerAgent
from app.models.user import User
from app.schemas.chat import ChatIntent, ChatRequest
from app.schemas.plan import PlanGenerateRequest


class MasterAgent:
    """Lightweight intent router for knowledge, plan, and general chat."""

    def __init__(self, db: AsyncSession) -> None:
        self.knowledge_agent = KnowledgeAgent(db)
        self.planner_agent = PlannerAgent(db)

    def detect_intent(self, message: str, document_id: object | None = None) -> ChatIntent:
        if document_id is not None:
            return ChatIntent.knowledge

        clean = message.strip().lower()
        if self._looks_like_plan_request(clean):
            return ChatIntent.plan
        if self._looks_like_knowledge_request(clean):
            return ChatIntent.knowledge
        return ChatIntent.general

    async def stream_answer(self, user: User, payload: ChatRequest) -> AsyncIterator[str]:
        intent = self.detect_intent(payload.message, payload.document_id)
        yield self._sse("start", {"message": payload.message, "intent": intent.value})

        if intent is ChatIntent.knowledge:
            response = await self.knowledge_agent.answer(user=user, payload=payload)
            yield self._sse(
                "content",
                {
                    "text": response.answer,
                    "intent": intent.value,
                    "is_placeholder": response.is_placeholder,
                    "answer_provider": response.answer_provider,
                    "model": response.model,
                },
            )
            yield self._sse(
                "citations",
                {
                    "sources": [source.model_dump(mode="json") for source in response.sources],
                    "context_text": response.context_text,
                },
            )
            yield self._sse("done", {"intent": intent.value, "source_count": len(response.sources)})
            return

        if intent is ChatIntent.plan:
            plan_response = await self.planner_agent.generate_plan(
                user=user,
                payload=PlanGenerateRequest(
                    goal=self._normalize_goal(payload.message),
                    days=self._extract_days(payload.message),
                    start_date=date.today(),
                ),
            )
            yield self._sse(
                "content",
                {
                    "text": plan_response.plan_text,
                    "intent": intent.value,
                    "created_tasks": [task.id for task in plan_response.created_tasks],
                },
            )
            yield self._sse(
                "done",
                {
                    "intent": intent.value,
                    "created_task_count": len(plan_response.created_tasks),
                },
            )
            return

        yield self._sse(
            "content",
            {
                "text": (
                    "我现在主要支持资料问答和复习计划。"
                    "你可以直接问课程资料，或者说“帮我生成 3 天复习计划”。"
                ),
                "intent": intent.value,
                "is_placeholder": True,
            },
        )
        yield self._sse("done", {"intent": intent.value, "source_count": 0})

    @staticmethod
    def _looks_like_plan_request(message: str) -> bool:
        plan_keywords = [
            "计划",
            "复习",
            "安排",
            "日程",
            "待办",
            "任务",
            "时间表",
            "schedule",
            "plan",
        ]
        return any(keyword in message for keyword in plan_keywords)

    @staticmethod
    def _looks_like_knowledge_request(message: str) -> bool:
        knowledge_keywords = [
            "pdf",
            "资料",
            "文档",
            "公式",
            "题目",
            "章节",
            "总结",
            "解释",
            "引用",
            "课件",
            "论文",
            "知识",
        ]
        return any(keyword in message for keyword in knowledge_keywords)

    @staticmethod
    def _normalize_goal(message: str) -> str:
        goal = message.strip()
        return goal[:255] if len(goal) > 255 else goal

    @staticmethod
    def _extract_days(message: str) -> int:
        match = re.search(r"(\d+)\s*天", message)
        if match:
            return max(1, min(30, int(match.group(1))))
        if any(keyword in message for keyword in ["一周", "7天", "七天", "week"]):
            return 7
        return 3

    @staticmethod
    def _sse(event: str, data: dict[str, object]) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
