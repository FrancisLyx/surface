from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.api.routes.fund.fund_schema import (
    FavoriteFundAddRequest,
    FavoriteFundAlertItem,
    FavoriteFundCheckResponse,
    FavoriteFundEstimationItem,
    FavoriteFundItem,
    FavoriteFundRemoveResponse,
    FavoriteFundReportExtreme,
    FavoriteFundReportResponse,
    FavoriteFundReportSummary,
)
from app.core.pagination import PageResponse
from app.db.models.fund_favorite import UserFavoriteFund
from app.db.models.user import User
from app.services import fund_service


def add_favorite_fund(db: Session, user: User, payload: FavoriteFundAddRequest) -> FavoriteFundItem:
    fund_code = payload.fund_code.strip()
    fund_name = payload.fund_name.strip()
    fund_type = payload.fund_type.strip() if payload.fund_type else None

    favorite = db.scalar(
        select(UserFavoriteFund).where(
            UserFavoriteFund.user_id == user.id,
            UserFavoriteFund.fund_code == fund_code,
        )
    )
    if favorite is None:
        favorite = UserFavoriteFund(
            user_id=user.id,
            fund_code=fund_code,
            fund_name=fund_name,
            fund_type=fund_type,
        )
        db.add(favorite)
    else:
        favorite.fund_name = fund_name
        favorite.fund_type = fund_type

    db.commit()
    db.refresh(favorite)
    return _to_item(favorite)


def list_favorite_funds(
    db: Session,
    user: User,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[FavoriteFundItem]:
    filters = [UserFavoriteFund.user_id == user.id]
    normalized_keyword = keyword.strip() if keyword else None
    if normalized_keyword:
        like_keyword = f"%{normalized_keyword}%"
        filters.append(
            or_(
                UserFavoriteFund.fund_code.ilike(like_keyword),
                UserFavoriteFund.fund_name.ilike(like_keyword),
                UserFavoriteFund.fund_type.ilike(like_keyword),
            )
        )

    where_clause = and_(*filters)
    total = db.scalar(select(func.count()).select_from(UserFavoriteFund).where(where_clause)) or 0
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    favorites = db.scalars(
        select(UserFavoriteFund)
        .where(where_clause)
        .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=[_to_item(favorite) for favorite in favorites],
    )


def list_favorite_fund_estimations(
    db: Session,
    user: User,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[FavoriteFundEstimationItem]:
    favorite_page = list_favorite_funds(db, user, keyword=keyword, page=page, page_size=page_size)
    estimations = {item.code: item for item in fund_service.list_all_fund_estimations("全部")}

    return PageResponse(
        page=favorite_page.page,
        page_size=favorite_page.page_size,
        total=favorite_page.total,
        pages=favorite_page.pages,
        items=[
            _to_estimation_item(favorite, estimations.get(favorite.fund_code))
            for favorite in favorite_page.items
        ],
    )


def get_favorite_fund_report(
    db: Session,
    user: User,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> FavoriteFundReportResponse:
    favorite_page = list_favorite_fund_estimations(db, user, keyword=keyword, page=page, page_size=page_size)
    items = favorite_page.items
    alerts = _build_alerts(items)
    estimated_items = [item for item in items if item.has_estimation]
    up_items = [item for item in estimated_items if _parse_percent(item.estimated_growth_rate) > 0]
    down_items = [item for item in estimated_items if _parse_percent(item.estimated_growth_rate) < 0]
    flat_items = [item for item in estimated_items if _parse_percent(item.estimated_growth_rate) == 0]

    summary = FavoriteFundReportSummary(
        total=favorite_page.total,
        estimated_count=len(estimated_items),
        up_count=len(up_items),
        down_count=len(down_items),
        flat_count=len(flat_items),
        missing_count=len(items) - len(estimated_items),
        alert_count=len(alerts),
        max_up=_build_extreme(max(up_items, key=lambda item: _parse_percent(item.estimated_growth_rate), default=None)),
        max_down=_build_extreme(min(down_items, key=lambda item: _parse_percent(item.estimated_growth_rate), default=None)),
    )
    return FavoriteFundReportResponse(summary=summary, alerts=alerts, page=favorite_page)


def check_favorite_fund(db: Session, user: User, fund_code: str) -> FavoriteFundCheckResponse:
    normalized_code = fund_code.strip()
    favorite_id = db.scalar(
        select(UserFavoriteFund.id).where(
            UserFavoriteFund.user_id == user.id,
            UserFavoriteFund.fund_code == normalized_code,
        )
    )
    return FavoriteFundCheckResponse(favorited=favorite_id is not None)


def remove_favorite_fund(db: Session, user: User, fund_code: str) -> FavoriteFundRemoveResponse:
    normalized_code = fund_code.strip()
    result = db.execute(
        delete(UserFavoriteFund).where(
            UserFavoriteFund.user_id == user.id,
            UserFavoriteFund.fund_code == normalized_code,
        )
    )
    db.commit()
    return FavoriteFundRemoveResponse(removed=(result.rowcount or 0) > 0)


def _to_item(favorite: UserFavoriteFund) -> FavoriteFundItem:
    return FavoriteFundItem(
        id=favorite.id,
        fund_code=favorite.fund_code,
        fund_name=favorite.fund_name,
        fund_type=favorite.fund_type,
        created_at=favorite.created_at.isoformat(),
    )


def _to_estimation_item(favorite: FavoriteFundItem, estimation) -> FavoriteFundEstimationItem:
    if estimation is None:
        return FavoriteFundEstimationItem(
            **favorite.model_dump(),
            estimate_date=None,
            estimated_nav=None,
            estimated_growth_rate=None,
            published_date=None,
            published_nav=None,
            published_growth_rate=None,
            estimate_deviation=None,
            previous_nav_date=None,
            previous_nav=None,
            has_estimation=False,
        )

    return FavoriteFundEstimationItem(
        **favorite.model_dump(),
        estimate_date=estimation.estimate_date,
        estimated_nav=estimation.estimated_nav,
        estimated_growth_rate=estimation.estimated_growth_rate,
        published_date=estimation.published_date,
        published_nav=estimation.published_nav,
        published_growth_rate=estimation.published_growth_rate,
        estimate_deviation=estimation.estimate_deviation,
        previous_nav_date=estimation.previous_nav_date,
        previous_nav=estimation.previous_nav,
        has_estimation=True,
    )


def _build_alerts(items: list[FavoriteFundEstimationItem]) -> list[FavoriteFundAlertItem]:
    alerts: list[FavoriteFundAlertItem] = []
    for item in items:
        if not item.has_estimation:
            alerts.append(
                FavoriteFundAlertItem(
                    fund_code=item.fund_code,
                    fund_name=item.fund_name,
                    level="warning",
                    message="暂无净值估算",
                )
            )
            continue

        growth_rate = _parse_percent(item.estimated_growth_rate)
        if growth_rate >= 2:
            alerts.append(
                FavoriteFundAlertItem(
                    fund_code=item.fund_code,
                    fund_name=item.fund_name,
                    level="warning",
                    message=f"估算涨幅 {_format_percent(item.estimated_growth_rate)}",
                )
            )
        elif growth_rate <= -2:
            alerts.append(
                FavoriteFundAlertItem(
                    fund_code=item.fund_code,
                    fund_name=item.fund_name,
                    level="warning",
                    message=f"估算跌幅 {_format_percent(item.estimated_growth_rate)}",
                )
            )

        deviation = _parse_percent(item.estimate_deviation)
        if abs(deviation) >= 2:
            alerts.append(
                FavoriteFundAlertItem(
                    fund_code=item.fund_code,
                    fund_name=item.fund_name,
                    level="warning",
                    message=f"估算偏差 {_format_percent(item.estimate_deviation)}",
                )
            )

    return alerts


def _build_extreme(item: FavoriteFundEstimationItem | None) -> FavoriteFundReportExtreme | None:
    if item is None:
        return None
    return FavoriteFundReportExtreme(
        fund_code=item.fund_code,
        fund_name=item.fund_name,
        rate=_format_percent(item.estimated_growth_rate),
    )


def _parse_percent(value: str | None) -> float:
    if not value or value == "---":
        return 0
    normalized = value.strip().replace("%", "")
    try:
        return float(normalized)
    except ValueError:
        return 0


def _format_percent(value: str | None) -> str:
    if not value:
        return "-"
    trimmed = value.strip()
    if not trimmed or trimmed == "---" or trimmed.endswith("%"):
        return trimmed or "-"
    return f"{trimmed}%"
