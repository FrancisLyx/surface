from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.outbox.repository import OutboxRepository
from app.modules.agent.repository import AgentRepository


class AgentUnitOfWork(SqlAlchemyUnitOfWork):
    def _setup_repositories(self, session: AsyncSession) -> None:
        self.agents = AgentRepository(session)
        self.outbox = OutboxRepository(session)
