from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.outbox.repository import OutboxRepository
from app.modules.ai.report_repository import AiFundReportRepository


class AiUnitOfWork(SqlAlchemyUnitOfWork):
    def _setup_repositories(self, session: AsyncSession) -> None:
        self.ai_fund_reports = AiFundReportRepository(session)
        self.outbox = OutboxRepository(session)
