from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
import app.infrastructure.inbox.models  # noqa: F401
import app.infrastructure.outbox.models  # noqa: F401
import app.modules.agent.models  # noqa: F401
import app.modules.ai.models  # noqa: F401
import app.modules.fund.models  # noqa: F401
import app.modules.settings.models  # noqa: F401
import app.modules.user.models  # noqa: F401


def _to_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url.replace(
            "postgresql+psycopg://", "postgresql+psycopg_async://", 1
        )
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return database_url


engine = create_async_engine(
    _to_async_database_url(get_settings().database_url), pool_pre_ping=True
)
SessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def init_db() -> None:
    """Database schema is managed by Alembic migrations, not application startup."""
    return None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        yield db
