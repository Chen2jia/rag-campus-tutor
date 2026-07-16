from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    total_chunks: int
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    task_id: UUID
    filename: str
    status: str


class DocumentStatusResponse(BaseModel):
    task_id: UUID
    status: str
    total_chunks: int
    error_message: str | None


class DocumentChunkSearchResult(BaseModel):
    id: UUID
    document_id: UUID
    filename: str
    chunk_index: int
    path: str
    section: str
    text: str
    page_start: int
    page_end: int
    contains_formula: bool
    formulas_metadata: list[dict[str, object]]

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkSearchResponse(BaseModel):
    query: str
    total: int
    results: list[DocumentChunkSearchResult]


class DeleteResponse(BaseModel):
    success: bool
