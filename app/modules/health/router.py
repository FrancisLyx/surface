from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.readiness import ReadinessState
from app.core.response import ApiResponse, success_response
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=ApiResponse, summary="存活检查")
def liveness_check(request: Request) -> ApiResponse:
    return success_response(
        request,
        {
            "status": "ok",
            "service": "alive",
        },
    )


@router.get("/ready", response_model=ApiResponse, summary="就绪检查")
async def readiness_check(
    request: Request, db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    readiness = _get_readiness_state(request)
    try:
        result = await db.execute(text("select 1"))
        result.scalar_one()
    except Exception as exc:
        readiness.mark_failed("database", str(exc))
        raise
    readiness.mark_ok("database")
    return success_response(
        request,
        {
            "status": "ok",
            "database": "ok",
        },
    )


@router.get("/startup", response_model=ApiResponse, summary="启动检查")
def startup_check(request: Request) -> ApiResponse:
    startup_complete = bool(getattr(request.app.state, "startup_complete", True))
    return success_response(
        request,
        {
            "status": "ok" if startup_complete else "starting",
            "startup_complete": startup_complete,
        },
    )


@router.get("", response_model=ApiResponse, summary="健康检查")
async def health_check(
    request: Request, db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    return await readiness_check(request, db)


def _get_readiness_state(request: Request) -> ReadinessState:
    readiness = getattr(request.app.state, "readiness", None)
    if readiness is None:
        readiness = ReadinessState()
        request.app.state.readiness = readiness
    return readiness
