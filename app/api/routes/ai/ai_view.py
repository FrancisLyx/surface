from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.routes.ai.ai_schema import (
    AiFundReportDetailRequest,
    AiFundReportListRequest,
    AiFundSummaryRequest,
)
from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services import ai_fund_report_service, ai_fund_service

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[require_auth()])


@router.post("/funds/reports/list", response_model=ApiResponse, summary="查询 AI 基金报告列表")
def list_fund_reports(
    request: Request,
    payload: AiFundReportListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        ai_fund_report_service.list_reports(
            db,
            current_user,
            fund_code=payload.fund_code,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/funds/reports/detail", response_model=ApiResponse, summary="查询 AI 基金报告详情")
def get_fund_report_detail(
    request: Request,
    payload: AiFundReportDetailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(request, ai_fund_report_service.get_report_detail(db, current_user, payload.id))


@router.post("/funds/summary/stream", summary="流式生成基金 AI 解读")
def stream_fund_summary(
    payload: AiFundSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        _to_sse_and_save(
            chunks=ai_fund_service.stream_fund_summary(payload.fund_code),
            db=db,
            current_user=current_user,
            fund_code=payload.fund_code,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _to_sse_and_save(chunks: Iterator[str], db: Session, current_user: User, fund_code: str):
    report_chunks: list[str] = []
    for chunk in chunks:
        report_chunks.append(chunk)
        yield f"data: {_escape_sse_data(chunk)}\n\n"

    content = "".join(report_chunks)
    if content:
        ai_fund_report_service.create_report(db, current_user, fund_code, content)
    yield "event: done\ndata: [DONE]\n\n"


def _escape_sse_data(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\ndata: ")
