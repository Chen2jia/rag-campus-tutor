from fastapi import APIRouter

from app.agents.planner_agent import PlannerAgent
from app.core.deps import CurrentUser, DbSession
from app.schemas.plan import PlanGenerateRequest, PlanGenerateResponse

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/generate", response_model=PlanGenerateResponse)
async def generate_plan(
    payload: PlanGenerateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> PlanGenerateResponse:
    return await PlannerAgent(db).generate_plan(current_user, payload)
