from collections.abc import Callable

from sqlalchemy.orm import Session

from app.services.agent_service import AgentService
from app.db.uow import SqlAlchemyUnitOfWork
from app.services.ai_fund_report_service import AiFundReportService
from app.services.fund_favorite_service import FundFavoriteService
from app.services.system_setting_service import SystemSettingService
from app.services.user_service import UserService


def create_uow_factory(session_factory: Callable[[], Session]) -> Callable[[], SqlAlchemyUnitOfWork]:
    return lambda: SqlAlchemyUnitOfWork(session_factory)


def create_user_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> UserService:
    return UserService(uow_factory)


def create_system_setting_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> SystemSettingService:
    return SystemSettingService(uow_factory)


def create_fund_favorite_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> FundFavoriteService:
    return FundFavoriteService(uow_factory)


def create_ai_fund_report_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> AiFundReportService:
    return AiFundReportService(uow_factory)


def create_agent_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> AgentService:
    return AgentService(uow_factory)
