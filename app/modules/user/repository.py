from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_id(self, user_id: int) -> User | None:
        return await self._session.scalar(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )

    async def get_by_username(self, username: str) -> User | None:
        return await self._session.scalar(select(User).where(User.username == username))

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def get_by_phone(self, phone: str) -> User | None:
        return await self._session.scalar(select(User).where(User.phone == phone))

    async def get_by_account(self, account: str) -> User | None:
        return await self._session.scalar(
            select(User).where(
                or_(
                    User.username == account,
                    User.email == account.lower(),
                    User.phone == account,
                )
            )
        )

    def add(self, user: User) -> None:
        self._session.add(user)

    async def refresh(self, user: User) -> None:
        await self._session.refresh(user)
