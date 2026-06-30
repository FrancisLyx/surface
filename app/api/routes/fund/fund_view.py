from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.routes.fund.fund_schema import (
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
from app.core.security import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services import fund_favorite_service, fund_service

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
def add_favorite_fund(
    request: Request,
    payload: FavoriteFundAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(request, fund_favorite_service.add_favorite_fund(db, current_user, payload))


@router.post("/funds/favorites/list", response_model=ApiResponse, summary="查询我的自选基金")
def list_favorite_funds(
    request: Request,
    payload: FavoriteFundSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        fund_favorite_service.list_favorite_funds(
            db,
            current_user,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/funds/favorites/estimations", response_model=ApiResponse, summary="查询我的自选基金净值估算")
def list_favorite_fund_estimations(
    request: Request,
    payload: FavoriteFundSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        fund_favorite_service.list_favorite_fund_estimations(
            db,
            current_user,
            keyword=payload.keyword,
            page=payload.page,
            page_size=payload.page_size,
        ),
    )


@router.post("/funds/favorites/check", response_model=ApiResponse, summary="查询基金是否已自选")
def check_favorite_fund(
    request: Request,
    payload: FavoriteFundCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        fund_favorite_service.check_favorite_fund(db, current_user, payload.fund_code),
    )


@router.post("/funds/favorites/remove", response_model=ApiResponse, summary="移除自选基金")
def remove_favorite_fund(
    request: Request,
    payload: FavoriteFundCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    return success_response(
        request,
        fund_favorite_service.remove_favorite_fund(db, current_user, payload.fund_code),
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


@router.post("/funds/estimation", response_model=ApiResponse, summary="查询单只基金净值估算")
def get_fund_estimation(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_estimation(payload.symbol))


@router.post("/funds/detail", response_model=ApiResponse, summary="查询基金详情")
def get_fund_detail(request: Request, payload: FundSymbolRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_detail(payload.symbol))


@router.post("/funds/profile", response_model=ApiResponse, summary="查询基金画像")
def get_fund_profile(request: Request, payload: FundProfileRequest) -> ApiResponse:
    return success_response(request, fund_service.get_fund_profile(payload))
