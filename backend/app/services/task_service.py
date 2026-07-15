import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_tasks(
        self,
        user: User,
        is_done: bool | None = None,
        due_date: date | None = None,
    ) -> list[Task]:
        query = select(Task).where(Task.user_id == user.id)
        if is_done is not None:
            query = query.where(Task.is_done == is_done)
        if due_date is not None:
            query = query.where(Task.due_date == due_date)
        query = query.order_by(Task.is_done.asc(), Task.due_date.asc().nulls_last(), Task.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_task(self, user: User, payload: TaskCreate) -> Task:
        task = Task(
            user_id=user.id,
            title=payload.title.strip(),
            subject=payload.subject.strip() if payload.subject else None,
            priority=payload.priority,
            due_date=payload.due_date,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update_task(self, user: User, task_id: uuid.UUID, payload: TaskUpdate) -> Task:
        task = await self._get_user_task(user=user, task_id=task_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"] is not None:
            task.title = update_data["title"].strip()
        if "subject" in update_data:
            subject = update_data["subject"]
            task.subject = subject.strip() if subject else None
        if "priority" in update_data and update_data["priority"] is not None:
            task.priority = update_data["priority"]
        if "due_date" in update_data:
            task.due_date = update_data["due_date"]
        if "is_done" in update_data and update_data["is_done"] is not None:
            task.is_done = update_data["is_done"]

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, user: User, task_id: uuid.UUID) -> bool:
        task = await self._get_user_task(user=user, task_id=task_id)
        await self.db.delete(task)
        await self.db.commit()
        return True

    async def _get_user_task(self, user: User, task_id: uuid.UUID) -> Task:
        result = await self.db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
        task = result.scalar_one_or_none()
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return task
