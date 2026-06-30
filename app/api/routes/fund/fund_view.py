from fastapi import APIRouter, Request

from app.api.routes.fund.fund_schema import (
    FundEstimationSearchRequest,
    FundSearchRequest,
    FundSymbolRequest,
    FundValueRequest,
)
from app.core.response import ApiResponse, success_response
from app.services import fund_service

router = APIRouter(prefix="", tags=["fund"])


@router.post("/funds/list", response_model=ApiResponse, summary="查询基金列表")
def list_funds(request: Request, payload: FundSearchRequest) -> ApiResponse:
    return success_response(
        request,
        fund_service.list_funds(
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/funds/estimations/search", response_model=ApiResponse, summary="查询基金净值估算")
def list_fund_estimations(request: Request, payload: FundEstimationSearchRequest) -> ApiResponse:
    return success_response(
        request,
        fund_service.list_fund_estimations(
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
            category=payload.category,
        ),
    )


@router.post("/funds/value", response_model=ApiResponse, summary="按来源查询基金净值")
def get_fund_value(request: Request, payload: FundValueRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_value(payload))


@router.post("/funds/estimation", response_model=ApiResponse, summary="查询单只基金净值估算")
def get_fund_estimation(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_estimation(payload.symbol))


@router.post("/funds/detail", response_model=ApiResponse, summary="查询基金详情")
def get_fund_detail(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_detail(payload.symbol))
