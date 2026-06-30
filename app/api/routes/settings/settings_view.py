from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.routes.settings.settings_schema import RegistrationSettingRequest
from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.db.session import get_db
from app.services import system_setting_service

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[require_auth()])


@router.get("/registration", response_model=ApiResponse, summary="查询注册设置")
def get_registration_setting(request: Request, db: Session = Depends(get_db)) -> ApiResponse:
    return success_response(request, system_setting_service.get_registration_setting(db))


@router.post("/registration", response_model=ApiResponse, summary="更新注册设置")
def update_registration_setting(
    request: Request,
    payload: RegistrationSettingRequest,
    db: Session = Depends(get_db),
) -> ApiResponse:
    return success_response(request, system_setting_service.update_registration_setting(db, payload.enabled))
