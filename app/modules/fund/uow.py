from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.outbox.repository import OutboxRepository
from app.modules.fund.favorite_repository import FundFavoriteRepository


class FundUnitOfWork(SqlAlchemyUnitOfWork):
    def _setup_repositories(self, session: AsyncSession) -> None:
        self.fund_favorites = FundFavoriteRepository(session)
        self.outbox = OutboxRepository(session)
