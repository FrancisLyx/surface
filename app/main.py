from fastapi import FastAPI

from app.modules.agent.api import router as agent_router
from app.modules.fund.api import router as fund_router
from app.modules.health.api import router as health_router
from app.modules.ai.api import router as ai_router
from app.modules.settings.api import router as settings_router
from app.modules.user.api import router as user_router
from app.core.exception import register_exception_handlers
from app.core.lifespan import app_lifespan
from app.core.middleware import register_request_middleware


app = FastAPI(title="Surface API", lifespan=app_lifespan)
register_request_middleware(app)
register_exception_handlers(app)
app.include_router(health_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(fund_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
