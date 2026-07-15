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


class DeleteResponse(BaseModel):
    success: bool
