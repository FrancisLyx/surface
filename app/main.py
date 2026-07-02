from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.router import api_router
from app.core.lifespan import app_lifespan
from app.core.middleware import register_request_middleware


app = FastAPI(title="Surface API", lifespan=app_lifespan)
register_request_middleware(app)
register_error_handlers(app)
app.include_router(api_router)
