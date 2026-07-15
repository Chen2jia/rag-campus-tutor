from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    priority: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None
    is_done: bool | None = None


class TaskRead(BaseModel):
    id: UUID
    title: str
    subject: str | None
    priority: int
    due_date: date | None
    is_done: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeleteResponse(BaseModel):
    success: bool
