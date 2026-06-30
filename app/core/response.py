from typing import Any

from fastapi import Request
from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any | None = None
    request_id: str


def success_response(request: Request, data: Any) -> ApiResponse:
    return ApiResponse(
        code=200,
        message="success",
        data=data,
        request_id=_get_request_id(request),
    )


def error_response(request: Request, status_code: int, message: str) -> ApiResponse:
    return ApiResponse(
        code=status_code,
        message=message,
        data=None,
        request_id=_get_request_id(request),
    )


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")
