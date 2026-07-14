from fastapi import APIRouter

from app.modules.agent.router import router as agent_router
from app.modules.ai.router import router as ai_router
from app.modules.fund.router import router as fund_router
from app.modules.health.router import router as health_router
from app.modules.settings.router import router as settings_router
from app.modules.strategy.router import router as strategy_router
from app.modules.user.router import router as user_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(user_router)
api_router.include_router(fund_router)
api_router.include_router(strategy_router)
api_router.include_router(ai_router)
api_router.include_router(agent_router)
api_router.include_router(settings_router)
