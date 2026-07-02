from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api import dependencies
from app.infrastructure.database import session as db_session
from app.infrastructure.database.base import Base
from app.main import app


AsyncTestingSessionLocal = async_sessionmaker[AsyncSession]


def create_testing_session_factory() -> AsyncTestingSessionLocal:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    import anyio

    anyio.run(create_schema)
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def make_test_client() -> tuple[TestClient, AsyncTestingSessionLocal]:
    session_factory = create_testing_session_factory()

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            yield db

    app.dependency_overrides[db_session.get_db] = override_db
    app.dependency_overrides[dependencies.get_session_factory] = lambda: session_factory
    return TestClient(app), session_factory
