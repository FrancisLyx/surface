from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.outbox.repository import OutboxRepository
from app.modules.settings.repository import SystemSettingRepository


class SettingsUnitOfWork(SqlAlchemyUnitOfWork):
    def _setup_repositories(self, session: AsyncSession) -> None:
        self.system_settings = SystemSettingRepository(session)
        self.outbox = OutboxRepository(session)
