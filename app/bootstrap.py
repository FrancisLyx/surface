from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.report_service import AiFundReportService
from app.modules.fund.favorite_service import FundFavoriteService
from app.modules.fund.public import FundQueryFacade
from app.modules.agent.service import AgentService
from app.modules.agent.uow import AgentUnitOfWork
from app.modules.ai.uow import AiUnitOfWork
from app.modules.fund.uow import FundUnitOfWork
from app.modules.settings.public import RegistrationPolicy
from app.modules.settings.service import SystemSettingService
from app.modules.settings.uow import SettingsUnitOfWork
from app.modules.user.service import UserService
from app.modules.user.uow import UserUnitOfWork


def create_user_uow_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], UserUnitOfWork]:
    return lambda: UserUnitOfWork(session_factory)


def create_settings_uow_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], SettingsUnitOfWork]:
    return lambda: SettingsUnitOfWork(session_factory)


def create_fund_uow_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], FundUnitOfWork]:
    return lambda: FundUnitOfWork(session_factory)


def create_ai_uow_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], AiUnitOfWork]:
    return lambda: AiUnitOfWork(session_factory)


def create_agent_uow_factory(
    session_factory: Callable[[], AsyncSession],
) -> Callable[[], AgentUnitOfWork]:
    return lambda: AgentUnitOfWork(session_factory)


def create_user_service(
    uow_factory: Callable[[], UserUnitOfWork],
    registration_policy: RegistrationPolicy,
) -> UserService:
    return UserService(uow_factory, registration_policy)


def create_system_setting_service(
    uow_factory: Callable[[], SettingsUnitOfWork],
) -> SystemSettingService:
    return SystemSettingService(uow_factory)


def create_fund_favorite_service(
    uow_factory: Callable[[], FundUnitOfWork],
    fund_query: FundQueryFacade | None = None,
) -> FundFavoriteService:
    return FundFavoriteService(uow_factory, fund_query=fund_query)


def create_ai_fund_report_service(
    uow_factory: Callable[[], AiUnitOfWork],
) -> AiFundReportService:
    return AiFundReportService(uow_factory)


def create_agent_service(uow_factory: Callable[[], AgentUnitOfWork]) -> AgentService:
    return AgentService(uow_factory)
