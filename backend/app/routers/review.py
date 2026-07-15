from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.review import ReviewCreate, ReviewRate, ReviewRateResponse, ReviewRead
from app.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


@router.post("", response_model=ReviewRead, status_code=201)
async def create_review_item(
    payload: ReviewCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ReviewRead:
    return await ReviewService(db).create_review_item(current_user, payload)


@router.get("/today", response_model=list[ReviewRead])
async def list_today_reviews(
    current_user: CurrentUser,
    db: DbSession,
) -> list[ReviewRead]:
    return await ReviewService(db).list_today(current_user)


@router.put("/{review_id}/rate", response_model=ReviewRateResponse)
async def rate_review_item(
    review_id: UUID,
    payload: ReviewRate,
    current_user: CurrentUser,
    db: DbSession,
) -> ReviewRateResponse:
    return await ReviewService(db).rate_review_item(current_user, review_id, payload.score)
