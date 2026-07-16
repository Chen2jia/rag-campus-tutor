from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)
    document_id: UUID | None = None
