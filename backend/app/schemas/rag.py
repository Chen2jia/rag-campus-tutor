from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class RagAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=10)
    document_id: UUID | None = None


class RagSource(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    path: str
    page_start: int
    page_end: int
    contains_formula: bool


class RagAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[RagSource]
    context_text: str
    is_placeholder: bool = True
