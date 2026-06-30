from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.routes.user.user_schema import LoginResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.services import system_setting_service


def get_register_status(db: Session) -> dict[str, bool]:
    return system_setting_service.get_registration_setting(db)


def register_user(db: Session, payload: UserRegisterRequest) -> UserResponse:
    if not system_setting_service.is_user_registration_enabled(db):
        raise HTTPException(status_code=403, detail="registration is disabled")

    username = payload.username.strip()
    email = str(payload.email).strip().lower() if payload.email else None
    phone = payload.phone.strip() if payload.phone else None

    if _get_user_by_username(db, username) is not None:
        raise HTTPException(status_code=400, detail="username already exists")
    if email and _get_user_by_email(db, email) is not None:
        raise HTTPException(status_code=400, detail="email already exists")
    if phone and _get_user_by_phone(db, phone) is not None:
        raise HTTPException(status_code=400, detail="phone already exists")

    user = User(
        username=username,
        email=email,
        phone=phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_user_response(user)


def login_user(db: Session, payload: UserLoginRequest) -> LoginResponse:
    account = payload.account.strip()
    user = db.scalar(
        select(User).where(
            or_(
                User.username == account,
                User.email == account.lower(),
                User.phone == account,
            )
        )
    )
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid account or password")

    return LoginResponse(
        access_token=create_access_token(user),
        user=build_user_response(user),
    )


def build_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
    )


def _get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def _get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))
