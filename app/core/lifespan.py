from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import init_db


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.startup_complete = False
    init_db()
    app.state.startup_complete = True
    try:
        yield
    finally:
        app.state.startup_complete = False
