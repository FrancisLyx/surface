from collections.abc import AsyncIterator, Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_ai_fund_report_service, get_current_user_context
from app.modules.ai.schemas import (
    AiFundReportDetailRequest,
    AiFundReportListRequest,
    AiFundSummaryRequest,
)
from app.core.auth import require_auth
from app.core.current_user import CurrentUser
from app.core.response import ApiResponse, success_response
from app.modules.ai import service as ai_fund_service
from app.modules.ai.report_service import AiFundReportService

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[require_auth()])


@router.post(
    "/funds/reports/list", response_model=ApiResponse, summary="查询 AI 基金报告列表"
)
async def list_fund_reports(
    request: Request,
    payload: AiFundReportListRequest,
    report_service: Annotated[AiFundReportService, Depends(get_ai_fund_report_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await report_service.list_reports(
            current_user,
            fund_code=payload.fund_code,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post(
    "/funds/reports/detail", response_model=ApiResponse, summary="查询 AI 基金报告详情"
)
async def get_fund_report_detail(
    request: Request,
    payload: AiFundReportDetailRequest,
    report_service: Annotated[AiFundReportService, Depends(get_ai_fund_report_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request, await report_service.get_report_detail(current_user, payload.id)
    )


@router.post("/funds/summary/stream", summary="流式生成基金 AI 解读")
def stream_fund_summary(
    payload: AiFundSummaryRequest,
    report_service: Annotated[AiFundReportService, Depends(get_ai_fund_report_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> StreamingResponse:
    return StreamingResponse(
        _to_sse_and_save(
            chunks=ai_fund_service.stream_fund_summary(payload.fund_code),
            report_service=report_service,
            current_user=current_user,
            fund_code=payload.fund_code,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _to_sse_and_save(
    chunks: Iterator[str],
    report_service: AiFundReportService,
    current_user: CurrentUser,
    fund_code: str,
) -> AsyncIterator[str]:
    report_chunks: list[str] = []
    for chunk in chunks:
        report_chunks.append(chunk)
        yield f"data: {_escape_sse_data(chunk)}\n\n"

    content = "".join(report_chunks)
    if content:
        await report_service.create_report(current_user, fund_code, content)
    yield "event: done\ndata: [DONE]\n\n"


def _escape_sse_data(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\ndata: ")
