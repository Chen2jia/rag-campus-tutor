from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.schemas.plan import PlanDay, PlanGenerateRequest, PlanGenerateResponse
from app.schemas.task import TaskCreate
from app.services.task_service import TaskService


class PlannerAgent:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.task_service = TaskService(db)

    async def generate_plan(self, user: User, payload: PlanGenerateRequest) -> PlanGenerateResponse:
        start_date = payload.start_date or date.today()
        plan_days = self._build_placeholder_plan(payload=payload, start_date=start_date)
        created_tasks: list[Task] = []

        for plan_day in plan_days:
            task = await self.task_service.create_task(
                user=user,
                payload=TaskCreate(
                    title=plan_day.title,
                    subject=payload.subject,
                    priority=3,
                    due_date=plan_day.date,
                ),
            )
            created_tasks.append(task)

        return PlanGenerateResponse(
            plan_text=self._format_plan_text(goal=payload.goal, plan_days=plan_days),
            days=plan_days,
            created_tasks=created_tasks,
        )

    @staticmethod
    def _build_placeholder_plan(
        payload: PlanGenerateRequest,
        start_date: date,
    ) -> list[PlanDay]:
        goal = payload.goal.strip()
        plan_days: list[PlanDay] = []
        for index in range(payload.days):
            day_number = index + 1
            current_date = start_date + timedelta(days=index)
            if day_number == payload.days:
                action = "总结复盘并完成综合练习"
            elif day_number == 1:
                action = "梳理核心概念并完成基础练习"
            else:
                action = "推进重点内容并整理错题"

            plan_days.append(
                PlanDay(
                    day=day_number,
                    date=current_date,
                    title=f"{goal} - Day {day_number}",
                    description=action,
                )
            )
        return plan_days

    @staticmethod
    def _format_plan_text(goal: str, plan_days: list[PlanDay]) -> str:
        lines = [f"【复习计划：{goal.strip()}】"]
        for plan_day in plan_days:
            lines.append(
                f"Day {plan_day.day}（{plan_day.date.isoformat()}）：{plan_day.description}"
            )
        return "\n".join(lines)
