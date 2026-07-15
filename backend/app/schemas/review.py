from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    knowledge_point: str = Field(min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    next_review_date: date | None = None


class ReviewRate(BaseModel):
    score: int = Field(ge=1, le=5)


class ReviewRead(BaseModel):
    id: UUID
    knowledge_point: str
    subject: str | None
    interval_days: int
    next_review_date: date
    ease_factor: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewRateResponse(BaseModel):
    item: ReviewRead
    score: int
    next_interval_days: int
    next_review_date: date
