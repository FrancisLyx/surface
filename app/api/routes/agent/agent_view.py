from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_agent_service, get_current_user_context
from app.api.routes.agent.agent_schema import (
    AgentListRequest,
    AgentChatStreamRequest,
    AgentConversationDetailRequest,
    AgentConversationListRequest,
    AgentReportDetailRequest,
    AgentReportListRequest,
)
from app.core.auth import require_auth
from app.core.current_user import CurrentUser
from app.core.response import ApiResponse, success_response
from app.services.agent_service import AgentService
from app.services.agent_event import AgentStreamEvent, encode_event_data

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[require_auth()])


@router.post("/list", response_model=ApiResponse, summary="查询可用智能体")
def list_agents(
    request: Request,
    payload: AgentListRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, service.list_agents(current_user, page=payload.page, page_size=payload.page_size))


@router.post("/chat/stream", summary="流式智能体对话")
def stream_agent_chat(
    payload: AgentChatStreamRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> StreamingResponse:
    return StreamingResponse(
        _to_sse(
            service.stream_chat(
                current_user,
                agent_id=payload.agent_id,
                message=payload.message,
                conversation_id=payload.conversation_id,
                fund_code=payload.fund_code,
            )
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/reports/list", response_model=ApiResponse, summary="查询智能体报告列表")
def list_reports(
    request: Request,
    payload: AgentReportListRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        service.list_reports(
            current_user,
            agent_id=payload.agent_id,
            target_code=payload.target_code,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/conversations/list", response_model=ApiResponse, summary="查询智能体会话列表")
def list_conversations(
    request: Request,
    payload: AgentConversationListRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        service.list_conversations(
            current_user,
            agent_id=payload.agent_id,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/conversations/detail", response_model=ApiResponse, summary="查询智能体会话详情")
def get_conversation_detail(
    request: Request,
    payload: AgentConversationDetailRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, service.get_conversation_detail(current_user, payload.conversation_id))


@router.post("/reports/detail", response_model=ApiResponse, summary="查询智能体报告详情")
def get_report_detail(
    request: Request,
    payload: AgentReportDetailRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, service.get_report_detail(current_user, payload.id))


def _to_sse(chunks: Iterator[AgentStreamEvent]):
    for chunk in chunks:
        yield f"event: {chunk.event}\ndata: {_escape_sse_data(encode_event_data(chunk.data))}\n\n"
    yield "event: done\ndata: [DONE]\n\n"


def _escape_sse_data(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\ndata: ")
