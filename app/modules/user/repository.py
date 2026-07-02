from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.user.model import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_by_id(self, user_id: int) -> User | None:
        return self._session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))

    def get_by_username(self, username: str) -> User | None:
        return self._session.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))

    def get_by_phone(self, phone: str) -> User | None:
        return self._session.scalar(select(User).where(User.phone == phone))

    def get_by_account(self, account: str) -> User | None:
        return self._session.scalar(
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

    def refresh(self, user: User) -> None:
        self._session.refresh(user)
