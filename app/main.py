from fastapi import FastAPI

from app.api.routes.fund.fund_view import router as fund_router
from app.api.routes.health.health_view import router as health_router
from app.core.exception import register_exception_handlers
from app.core.middleware import register_request_middleware

app = FastAPI(title="Surface API")
register_request_middleware(app)
register_exception_handlers(app)
app.include_router(health_router, prefix="/api/v1")
app.include_router(fund_router, prefix="/api/v1")
