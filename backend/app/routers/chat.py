from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.knowledge_agent import KnowledgeAgent
from app.core.deps import CurrentUser, DbSession
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> StreamingResponse:
    return StreamingResponse(
        KnowledgeAgent(db).stream_answer(current_user, payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
