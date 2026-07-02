from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_current_user_context, get_fund_favorite_service
from app.modules.fund.schemas import (
    FavoriteFundAddRequest,
    FavoriteFundCodeRequest,
    FavoriteFundSearchRequest,
    FundEstimationSearchRequest,
    FundProfileRequest,
    FundRankSearchRequest,
    FundSearchRequest,
    FundSymbolRequest,
    FundValueRequest,
)
from app.core.response import ApiResponse, success_response
from app.core.auth import require_auth
from app.core.current_user import CurrentUser
from app.modules.fund import service as fund_service
from app.modules.fund.favorite_service import FundFavoriteService

router = APIRouter(prefix="", tags=["fund"], dependencies=[require_auth()])


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


@router.post("/funds/favorites/add", response_model=ApiResponse, summary="添加自选基金")
async def add_favorite_fund(
    request: Request,
    payload: FavoriteFundAddRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request, await service.add_favorite_fund(current_user, payload)
    )


@router.post(
    "/funds/favorites/list", response_model=ApiResponse, summary="查询我的自选基金"
)
async def list_favorite_funds(
    request: Request,
    payload: FavoriteFundSearchRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await service.list_favorite_funds(
            current_user,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post(
    "/funds/favorites/options",
    response_model=ApiResponse,
    summary="查询我的自选基金选项",
)
async def list_favorite_fund_options(
    request: Request,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request, await service.list_favorite_fund_options(current_user)
    )


@router.post(
    "/funds/favorites/estimations",
    response_model=ApiResponse,
    summary="查询我的自选基金净值估算",
)
async def list_favorite_fund_estimations(
    request: Request,
    payload: FavoriteFundSearchRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await service.list_favorite_fund_estimations(
            current_user,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post(
    "/funds/favorites/report",
    response_model=ApiResponse,
    summary="查询我的自选基金日报",
)
async def get_favorite_fund_report(
    request: Request,
    payload: FavoriteFundSearchRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await service.get_favorite_fund_report(
            current_user,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post(
    "/funds/favorites/check", response_model=ApiResponse, summary="查询基金是否已自选"
)
async def check_favorite_fund(
    request: Request,
    payload: FavoriteFundCodeRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await service.check_favorite_fund(current_user, payload.fund_code),
    )


@router.post(
    "/funds/favorites/remove", response_model=ApiResponse, summary="移除自选基金"
)
async def remove_favorite_fund(
    request: Request,
    payload: FavoriteFundCodeRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(
        request,
        await service.remove_favorite_fund(current_user, payload.fund_code),
    )


@router.post(
    "/funds/estimations/search", response_model=ApiResponse, summary="查询基金净值估算"
)
def list_fund_estimations(
    request: Request, payload: FundEstimationSearchRequest
) -> ApiResponse:
    return success_response(
        request,
        fund_service.list_fund_estimations(
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
            category=payload.category,
        ),
    )


@router.post("/funds/rank", response_model=ApiResponse, summary="查询开放基金排行")
def list_fund_rank(request: Request, payload: FundRankSearchRequest) -> ApiResponse:
    return success_response(
        request,
        fund_service.list_fund_rank(
            category=payload.category,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/funds/value", response_model=ApiResponse, summary="按来源查询基金净值")
def get_fund_value(request: Request, payload: FundValueRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_value(payload))


@router.post(
    "/funds/estimation", response_model=ApiResponse, summary="查询单只基金净值估算"
)
def get_fund_estimation(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_estimation(payload.symbol))


@router.post("/funds/detail", response_model=ApiResponse, summary="查询基金详情")
def get_fund_detail(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_detail(payload.symbol))


@router.post("/funds/profile", response_model=ApiResponse, summary="查询基金画像")
def get_fund_profile(request: Request, payload: FundProfileRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_profile(payload))
