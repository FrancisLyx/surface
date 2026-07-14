from fastapi import APIRouter, Request

from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.modules.strategy import service as strategy_service
from app.modules.strategy.schemas import StrategyAnalyzeRequest

router = APIRouter(
    prefix="/strategies", tags=["strategy"], dependencies=[require_auth()]
)


@router.post(
    "/analyze",
    response_model=ApiResponse,
    summary="按分析类型执行策略分析",
)
def analyze_strategy(request: Request, payload: StrategyAnalyzeRequest) -> ApiResponse:
    return success_response(request, strategy_service.analyze_strategy(payload))
