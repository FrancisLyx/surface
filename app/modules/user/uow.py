from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.outbox.repository import OutboxRepository
from app.modules.user.repository import UserRepository


class UserUnitOfWork(SqlAlchemyUnitOfWork):
    def _setup_repositories(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)
        self.outbox = OutboxRepository(session)
