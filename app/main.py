from fastapi import FastAPI

from app.api.routes.agent.agent_view import router as agent_router
from app.api.routes.fund.fund_view import router as fund_router
from app.api.routes.health.health_view import router as health_router
from app.api.routes.ai.ai_view import router as ai_router
from app.api.routes.settings.settings_view import router as settings_router
from app.api.routes.user.user_view import router as user_router
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
