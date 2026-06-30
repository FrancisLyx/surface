import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    database_url: str = "postgresql+psycopg://surface:surface@127.0.0.1:5432/surface"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://surface:surface@127.0.0.1:5432/surface",
        ),
    )
