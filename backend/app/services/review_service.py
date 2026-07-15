import uuid
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import ReviewSchedule
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRateResponse


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_review_item(self, user: User, payload: ReviewCreate) -> ReviewSchedule:
        item = ReviewSchedule(
            user_id=user.id,
            knowledge_point=payload.knowledge_point.strip(),
            subject=payload.subject.strip() if payload.subject else None,
            next_review_date=payload.next_review_date or date.today(),
            interval_days=1,
            ease_factor=2.5,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_today(self, user: User, today: date | None = None) -> list[ReviewSchedule]:
        target_date = today or date.today()
        result = await self.db.execute(
            select(ReviewSchedule)
            .where(
                ReviewSchedule.user_id == user.id,
                ReviewSchedule.next_review_date <= target_date,
            )
            .order_by(ReviewSchedule.next_review_date.asc(), ReviewSchedule.created_at.desc())
        )
        return list(result.scalars().all())

    async def rate_review_item(
        self,
        user: User,
        review_id: uuid.UUID,
        score: int,
    ) -> ReviewRateResponse:
        item = await self._get_user_review_item(user=user, review_id=review_id)
        next_interval, next_ease_factor = self._calculate_sm2(
            score=score,
            current_interval=item.interval_days,
            current_ease_factor=item.ease_factor,
        )

        item.interval_days = next_interval
        item.ease_factor = next_ease_factor
        item.next_review_date = date.today() + timedelta(days=next_interval)

        await self.db.commit()
        await self.db.refresh(item)

        return ReviewRateResponse(
            item=item,
            score=score,
            next_interval_days=item.interval_days,
            next_review_date=item.next_review_date,
        )

    async def _get_user_review_item(self, user: User, review_id: uuid.UUID) -> ReviewSchedule:
        result = await self.db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.id == review_id,
                ReviewSchedule.user_id == user.id,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found",
            )
        return item

    @staticmethod
    def _calculate_sm2(
        score: int,
        current_interval: int,
        current_ease_factor: float,
    ) -> tuple[int, float]:
        if score < 3:
            return 1, max(1.3, current_ease_factor - 0.2)

        next_ease_factor = current_ease_factor + (
            0.1 - (5 - score) * (0.08 + (5 - score) * 0.02)
        )
        next_ease_factor = max(1.3, next_ease_factor)

        if current_interval <= 1:
            next_interval = 1 if score == 3 else 3
        else:
            next_interval = round(current_interval * next_ease_factor)

        return max(1, next_interval), round(next_ease_factor, 2)
