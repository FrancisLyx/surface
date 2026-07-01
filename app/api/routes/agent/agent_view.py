from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.routes.agent.agent_schema import (
    AgentListRequest,
    AgentChatStreamRequest,
    AgentConversationDetailRequest,
    AgentConversationListRequest,
    AgentReportDetailRequest,
    AgentReportListRequest,
)
from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services import agent_service
from app.services.agent_event import AgentStreamEvent, encode_event_data

router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[require_auth()])


@router.post("/list", response_model=ApiResponse, summary="查询可用智能体")
def list_agents(
    request: Request,
    payload: AgentListRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(request, agent_service.list_agents(db, current_user, page=payload.page, page_size=payload.page_size))


@router.post("/chat/stream", summary="流式智能体对话")
def stream_agent_chat(
    payload: AgentChatStreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    return StreamingResponse(
        _to_sse(
            agent_service.stream_chat(
                db,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        agent_service.list_reports(
            db,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        agent_service.list_conversations(
            db,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(request, agent_service.get_conversation_detail(db, current_user, payload.conversation_id))


@router.post("/reports/detail", response_model=ApiResponse, summary="查询智能体报告详情")
def get_report_detail(
    request: Request,
    payload: AgentReportDetailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(request, agent_service.get_report_detail(db, current_user, payload.id))


def _to_sse(chunks: Iterator[AgentStreamEvent]):
    for chunk in chunks:
        yield f"event: {chunk.event}\ndata: {_escape_sse_data(encode_event_data(chunk.data))}\n\n"
    yield "event: done\ndata: [DONE]\n\n"


def _escape_sse_data(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\ndata: ")
