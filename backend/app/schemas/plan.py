from datetime import date

from pydantic import BaseModel, Field

from app.schemas.task import TaskRead


class PlanGenerateRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=255)
    days: int = Field(ge=1, le=30)
    subject: str | None = Field(default=None, max_length=64)
    start_date: date | None = None


class PlanDay(BaseModel):
    day: int
    date: date
    title: str
    description: str


class PlanGenerateResponse(BaseModel):
    plan_text: str
    days: list[PlanDay]
    created_tasks: list[TaskRead]
