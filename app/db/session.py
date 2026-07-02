from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
import app.modules.agent.model  # noqa: F401
import app.modules.ai.report_model  # noqa: F401
import app.modules.fund.favorite_model  # noqa: F401
import app.modules.settings.model  # noqa: F401
import app.modules.user.model  # noqa: F401

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
