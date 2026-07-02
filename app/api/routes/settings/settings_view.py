from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_system_setting_service
from app.api.routes.settings.settings_schema import RegistrationSettingRequest
from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.services.system_setting_service import SystemSettingService

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[require_auth()])


@router.get("/registration", response_model=ApiResponse, summary="查询注册设置")
def get_registration_setting(
    request: Request,
    service: Annotated[SystemSettingService, Depends(get_system_setting_service)],
) -> ApiResponse:
    return success_response(request, service.get_registration_setting())


@router.post("/registration", response_model=ApiResponse, summary="更新注册设置")
def update_registration_setting(
    request: Request,
    payload: RegistrationSettingRequest,
    service: Annotated[SystemSettingService, Depends(get_system_setting_service)],
) -> ApiResponse:
    return success_response(request, service.update_registration_setting(payload.enabled))
