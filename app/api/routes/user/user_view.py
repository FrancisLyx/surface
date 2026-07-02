from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_current_user_context, get_user_service
from app.api.routes.user.user_schema import UserLoginRequest, UserRegisterRequest
from app.core.current_user import CurrentUser
from app.core.response import ApiResponse, success_response
from app.services.user_service import UserService, build_user_response

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/register-status", response_model=ApiResponse, summary="查询注册开关")
def get_register_status(
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.get_register_status())


@router.post("/register", response_model=ApiResponse, summary="用户注册")
def register_user(
    request: Request,
    payload: UserRegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.register_user(payload))


@router.post("/login", response_model=ApiResponse, summary="用户登录")
def login_user(
    request: Request,
    payload: UserLoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.login_user(payload))


@router.get("/me", response_model=ApiResponse, summary="当前用户")
def get_me(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, build_user_response(current_user))
