from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession
from app.schemas.task import DeleteResponse, TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    current_user: CurrentUser,
    db: DbSession,
    is_done: bool | None = Query(default=None),
    due_date: date | None = Query(default=None),
) -> list[TaskRead]:
    return await TaskService(db).list_tasks(
        user=current_user,
        is_done=is_done,
        due_date=due_date,
    )


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskRead:
    return await TaskService(db).create_task(current_user, payload)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskRead:
    return await TaskService(db).update_task(current_user, task_id, payload)


@router.delete("/{task_id}", response_model=DeleteResponse)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DeleteResponse:
    success = await TaskService(db).delete_task(current_user, task_id)
    return DeleteResponse(success=success)
