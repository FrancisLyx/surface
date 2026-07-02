from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from app.modules.agent.repository import AgentRepository
from app.modules.ai.report_repository import AiFundReportRepository
from app.modules.fund.favorite_repository import FundFavoriteRepository
from app.modules.settings.repository import SystemSettingRepository
from app.modules.user.repository import UserRepository


SessionFactory = Callable[[], Session]


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self._committed = False
        self.users = UserRepository(self._session)
        self.system_settings = SystemSettingRepository(self._session)
        self.fund_favorites = FundFavoriteRepository(self._session)
        self.ai_fund_reports = AiFundReportRepository(self._session)
        self.agents = AgentRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is not None or not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of Work is not active")
        return self._session

    def commit(self) -> None:
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
