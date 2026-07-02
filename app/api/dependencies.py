from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.bootstrap import (
    create_ai_fund_report_service,
    create_fund_favorite_service,
    create_system_setting_service,
    create_uow_factory,
    create_user_service,
)
from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser
from app.core.security import bearer_scheme
from app.db.session import SessionLocal
from app.db.uow import SqlAlchemyUnitOfWork
from app.services.ai_fund_report_service import AiFundReportService
from app.services.fund_favorite_service import FundFavoriteService
from app.services.system_setting_service import SystemSettingService
from app.services.user_service import UserService

SettingsDep = Annotated[Settings, Depends(get_settings)]
UowFactory = Callable[[], SqlAlchemyUnitOfWork]


def get_uow_factory() -> UowFactory:
    return create_uow_factory(SessionLocal)


def get_user_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> UserService:
    return create_user_service(uow_factory)


def get_system_setting_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> SystemSettingService:
    return create_system_setting_service(uow_factory)


def get_fund_favorite_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> FundFavoriteService:
    return create_fund_favorite_service(uow_factory)


def get_ai_fund_report_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> AiFundReportService:
    return create_ai_fund_report_service(uow_factory)


def get_current_user_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDep,
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
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

    with uow_factory() as uow:
        user = uow.users.get_active_by_id(user_id)
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
