from datetime import datetime, timedelta, timezone

from fastapi.security import HTTPBearer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.db.models.user import User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user: User) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(*args, **kwargs):
    from app.api.dependencies import get_current_user_context

    return get_current_user_context(*args, **kwargs)
