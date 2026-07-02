from fastapi import FastAPI

from app.core.exception import register_exception_handlers


def register_error_handlers(app: FastAPI) -> None:
    register_exception_handlers(app)
