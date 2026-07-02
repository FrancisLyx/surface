from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from sqlalchemy import text

from app.core.readiness import ReadinessState, monitor_readiness
from app.infrastructure.database.session import SessionLocal, engine, init_db


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.startup_complete = False
    app.state.readiness = ReadinessState()
    await init_db()
    monitor_task: asyncio.Task[None] | None = None
    if not getattr(app.state, "testing", False):
        monitor_task = asyncio.create_task(
            monitor_readiness(
                app.state.readiness,
                {"database": _check_database},
            )
        )
    app.state.startup_complete = True
    try:
        yield
    finally:
        app.state.readiness.mark_failed("database", "shutdown")
        if monitor_task is not None:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        await engine.dispose()
        app.state.startup_complete = False


async def _check_database() -> None:
    async with SessionLocal() as session:
        result = await session.execute(text("select 1"))
        result.scalar_one()
