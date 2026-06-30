from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, success_response
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse, summary="健康检查")
def health_check(request: Request, db: Session = Depends(get_db)) -> ApiResponse:
    db.execute(text("select 1")).scalar_one()
    return success_response(
        request,
        {
            "status": "ok",
            "database": "ok",
        },
    )
