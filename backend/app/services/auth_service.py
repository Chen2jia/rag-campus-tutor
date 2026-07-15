from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: UserCreate) -> TokenResponse:
        username = payload.username.strip()
        email = payload.email.strip().lower()

        existing_user = await self._find_by_username_or_email(username=username, email=email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email is already registered",
            )

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(payload.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return self._token_response(user)

    async def login(self, payload: UserLogin) -> TokenResponse:
        email = payload.email.strip().lower()
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        return self._token_response(user)

    async def _find_by_username_or_email(self, username: str, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(or_(User.username == username, User.email == email))
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _token_response(user: User) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=access_token, user=user)
