from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap import (
    create_agent_service,
    create_agent_uow_factory,
    create_ai_uow_factory,
    create_ai_fund_report_service,
    create_fund_uow_factory,
    create_fund_favorite_service,
    create_settings_uow_factory,
    create_system_setting_service,
    create_user_uow_factory,
    create_user_service,
)
from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser
from app.core.security import bearer_scheme
from app.infrastructure.database.session import SessionLocal
from app.modules.agent.service import AgentService
from app.modules.agent.uow import AgentUnitOfWork
from app.modules.ai.report_service import AiFundReportService
from app.modules.ai.uow import AiUnitOfWork
from app.modules.fund.favorite_service import FundFavoriteService
from app.modules.fund.public import FundQueryFacade
from app.modules.fund.uow import FundUnitOfWork
from app.modules.settings.public import RegistrationPolicy
from app.modules.settings.service import SystemSettingService
from app.modules.settings.uow import SettingsUnitOfWork
from app.modules.user.service import UserService
from app.modules.user.uow import UserUnitOfWork

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionFactory = Callable[[], AsyncSession]
UserUowFactory = Callable[[], UserUnitOfWork]
SettingsUowFactory = Callable[[], SettingsUnitOfWork]
FundUowFactory = Callable[[], FundUnitOfWork]
AiUowFactory = Callable[[], AiUnitOfWork]
AgentUowFactory = Callable[[], AgentUnitOfWork]


def get_session_factory() -> SessionFactory:
    return SessionLocal


def get_user_uow_factory(
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> UserUowFactory:
    return create_user_uow_factory(session_factory)


def get_settings_uow_factory(
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> SettingsUowFactory:
    return create_settings_uow_factory(session_factory)


def get_fund_uow_factory(
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> FundUowFactory:
    return create_fund_uow_factory(session_factory)


def get_ai_uow_factory(
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> AiUowFactory:
    return create_ai_uow_factory(session_factory)


def get_agent_uow_factory(
    session_factory: Annotated[SessionFactory, Depends(get_session_factory)],
) -> AgentUowFactory:
    return create_agent_uow_factory(session_factory)


def get_registration_policy(
    uow_factory: Annotated[SettingsUowFactory, Depends(get_settings_uow_factory)],
) -> RegistrationPolicy:
    return RegistrationPolicy(uow_factory)


def get_fund_query_facade() -> FundQueryFacade:
    return FundQueryFacade()


def get_user_service(
    uow_factory: Annotated[UserUowFactory, Depends(get_user_uow_factory)],
    registration_policy: Annotated[
        RegistrationPolicy, Depends(get_registration_policy)
    ],
) -> UserService:
    return create_user_service(uow_factory, registration_policy)


def get_system_setting_service(
    uow_factory: Annotated[SettingsUowFactory, Depends(get_settings_uow_factory)],
) -> SystemSettingService:
    return create_system_setting_service(uow_factory)


def get_fund_favorite_service(
    uow_factory: Annotated[FundUowFactory, Depends(get_fund_uow_factory)],
    fund_query: Annotated[FundQueryFacade, Depends(get_fund_query_facade)],
) -> FundFavoriteService:
    return create_fund_favorite_service(uow_factory, fund_query)


def get_ai_fund_report_service(
    uow_factory: Annotated[AiUowFactory, Depends(get_ai_uow_factory)],
) -> AiFundReportService:
    return create_ai_fund_report_service(uow_factory)


def get_agent_service(
    uow_factory: Annotated[AgentUowFactory, Depends(get_agent_uow_factory)],
) -> AgentService:
    return create_agent_service(uow_factory)


async def get_current_user_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDep,
    uow_factory: Annotated[UserUowFactory, Depends(get_user_uow_factory)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = int(payload.get("sub", ""))
    except (JWTError, ValueError):
        raise _unauthorized() from None

    async with uow_factory() as uow:
        user = await uow.users.get_active_by_id(user_id)
        if user is None:
            raise _unauthorized()
        return CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
        )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
