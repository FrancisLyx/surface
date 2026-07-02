from collections.abc import Callable

from sqlalchemy.orm import Session

from app.modules.user.schema import LoginResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.core.current_user import CurrentUser
from app.core.exception import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.user.model import User
from app.db.uow import SqlAlchemyUnitOfWork
from app.modules.settings import service as system_setting_service


class UserService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def get_register_status(self) -> dict[str, bool]:
        with self._uow_factory() as uow:
            return {"enabled": uow.system_settings.is_registration_enabled()}

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        with self._uow_factory() as uow:
            if not uow.system_settings.is_registration_enabled():
                raise ForbiddenError("registration is disabled")

            username = payload.username.strip()
            email = str(payload.email).strip().lower() if payload.email else None
            phone = payload.phone.strip() if payload.phone else None

            if uow.users.get_by_username(username) is not None:
                raise ConflictError("username already exists")
            if email and uow.users.get_by_email(email) is not None:
                raise ConflictError("email already exists")
            if phone and uow.users.get_by_phone(phone) is not None:
                raise ConflictError("phone already exists")

            user = User(
                username=username,
                email=email,
                phone=phone,
                password_hash=hash_password(payload.password),
            )
            uow.users.add(user)
            uow.commit()
            uow.users.refresh(user)
            return build_user_response(user)

    def login_user(self, payload: UserLoginRequest) -> LoginResponse:
        account = payload.account.strip()
        with self._uow_factory() as uow:
            user = uow.users.get_by_account(account)
            if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
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


def _service_from_session(db: Session) -> UserService:
    return UserService(lambda: SqlAlchemyUnitOfWork(lambda: db))


def get_register_status(db: Session) -> dict[str, bool]:
    return system_setting_service.get_registration_setting(db)


def register_user(db: Session, payload: UserRegisterRequest) -> UserResponse:
    return _service_from_session(db).register_user(payload)


def login_user(db: Session, payload: UserLoginRequest) -> LoginResponse:
    return _service_from_session(db).login_user(payload)
