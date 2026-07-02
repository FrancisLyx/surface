from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import CurrentUser
from app.core.exception import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.settings.public import RegistrationPolicy
from app.modules.settings.uow import SettingsUnitOfWork
from app.modules.user.models import User
from app.modules.user.schemas import (
    LoginResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.modules.user.uow import UserUnitOfWork


class UserService:
    def __init__(
        self,
        uow_factory: Callable[[], UserUnitOfWork],
        registration_policy: RegistrationPolicy,
    ) -> None:
        self._uow_factory = uow_factory
        self._registration_policy = registration_policy

    async def get_register_status(self) -> dict[str, bool]:
        return {"enabled": await self._registration_policy.is_registration_enabled()}

    async def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        if not await self._registration_policy.is_registration_enabled():
            raise ForbiddenError("registration is disabled")

        async with self._uow_factory() as uow:
            username = payload.username.strip()
            email = str(payload.email).strip().lower() if payload.email else None
            phone = payload.phone.strip() if payload.phone else None

            if await uow.users.get_by_username(username) is not None:
                raise ConflictError("username already exists")
            if email and await uow.users.get_by_email(email) is not None:
                raise ConflictError("email already exists")
            if phone and await uow.users.get_by_phone(phone) is not None:
                raise ConflictError("phone already exists")

            user = User(
                username=username,
                email=email,
                phone=phone,
                password_hash=hash_password(payload.password),
            )
            uow.users.add(user)
            await uow.commit()
            await uow.users.refresh(user)
            return build_user_response(user)

    async def login_user(self, payload: UserLoginRequest) -> LoginResponse:
        account = payload.account.strip()
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_account(account)
            if (
                user is None
                or not user.is_active
                or not verify_password(payload.password, user.password_hash)
            ):
                raise UnauthorizedError("invalid account or password")

            return LoginResponse(
                access_token=create_access_token(user),
                user=build_user_response(user),
            )


def build_user_response(user: User | CurrentUser) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
    )


def _service_from_session(db: AsyncSession) -> UserService:
    def session_factory() -> AsyncSession:
        return db

    def settings_uow_factory() -> SettingsUnitOfWork:
        return SettingsUnitOfWork(session_factory)

    def user_uow_factory() -> UserUnitOfWork:
        return UserUnitOfWork(session_factory)

    return UserService(user_uow_factory, RegistrationPolicy(settings_uow_factory))


async def get_register_status(db: AsyncSession) -> dict[str, bool]:
    return await _service_from_session(db).get_register_status()


async def register_user(db: AsyncSession, payload: UserRegisterRequest) -> UserResponse:
    return await _service_from_session(db).register_user(payload)


async def login_user(db: AsyncSession, payload: UserLoginRequest) -> LoginResponse:
    return await _service_from_session(db).login_user(payload)
