from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.routes.user.user_schema import UserLoginRequest, UserRegisterRequest
from app.core.response import ApiResponse, success_response
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services import user_service

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/register-status", response_model=ApiResponse, summary="查询注册开关")
def get_register_status(request: Request) -> ApiResponse:
    return success_response(request, user_service.get_register_status())


@router.post("/register", response_model=ApiResponse, summary="用户注册")
def register_user(request: Request, payload: UserRegisterRequest, db: Session = Depends(get_db)) -> ApiResponse:
    return success_response(request, user_service.register_user(db, payload))


@router.post("/login", response_model=ApiResponse, summary="用户登录")
def login_user(request: Request, payload: UserLoginRequest, db: Session = Depends(get_db)) -> ApiResponse:
    return success_response(request, user_service.login_user(db, payload))


@router.get("/me", response_model=ApiResponse, summary="当前用户")
def get_me(request: Request, current_user: User = Depends(get_current_user)) -> ApiResponse:
    return success_response(request, user_service.build_user_response(current_user))
