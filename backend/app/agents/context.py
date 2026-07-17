from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.models.user import User
from app.schemas.chat import ChatRequest


@dataclass(frozen=True)
class AgentContext:
    """Shared runtime context passed through the agent graph."""

    user: User
    message: str
    limit: int
    document_id: UUID | None

    @classmethod
    def from_chat_request(cls, user: User, payload: ChatRequest) -> "AgentContext":
        return cls(
            user=user,
            message=payload.message.strip(),
            limit=payload.limit,
            document_id=payload.document_id,
        )
