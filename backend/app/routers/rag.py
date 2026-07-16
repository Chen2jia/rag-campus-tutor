from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.rag import RagAskRequest, RagAskResponse
from app.services.rag_service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=RagAskResponse)
async def ask_rag(
    payload: RagAskRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> RagAskResponse:
    return await RagService(db).ask(current_user, payload)
