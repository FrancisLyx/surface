import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    database_url: str = "postgresql+psycopg://surface:surface@127.0.0.1:5432/surface"
    jwt_secret_key: str = "surface-development-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://surface:surface@127.0.0.1:5432/surface",
        ),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "surface-development-secret"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
    )


def is_user_registration_enabled() -> bool:
    return os.getenv("USER_REGISTRATION_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
