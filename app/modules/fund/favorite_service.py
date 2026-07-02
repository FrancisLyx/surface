from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fund.schemas import (
    FavoriteFundAddRequest,
    FavoriteFundAlertItem,
    FavoriteFundCheckResponse,
    FavoriteFundEstimationItem,
    FavoriteFundItem,
    FavoriteFundOptionItem,
    FavoriteFundRemoveResponse,
    FavoriteFundReportExtreme,
    FavoriteFundReportResponse,
    FavoriteFundReportSummary,
)
from app.core.current_user import CurrentUser
from app.core.pagination import PageResponse
from app.modules.fund.models import UserFavoriteFund
from app.modules.fund.public import FundQueryFacade
from app.modules.fund.uow import FundUnitOfWork
from app.modules.user.models import User


class FundFavoriteService:
    def __init__(
        self,
        uow_factory: Callable[[], FundUnitOfWork],
        fund_query: FundQueryFacade | None = None,
        favorite_model: type = UserFavoriteFund,
    ) -> None:
        self._uow_factory = uow_factory
        self._fund_query = fund_query or FundQueryFacade()
        self._favorite_model = favorite_model

    async def add_favorite_fund(
        self, user: CurrentUser, payload: FavoriteFundAddRequest
    ) -> FavoriteFundItem:
        fund_code = payload.fund_code.strip()
        fund_name = payload.fund_name.strip()
        fund_type = payload.fund_type.strip() if payload.fund_type else None

        async with self._uow_factory() as uow:
            favorite = await uow.fund_favorites.get_by_user_and_code(user.id, fund_code)
            if favorite is None:
                favorite = self._favorite_model(
                    user_id=user.id,
                    fund_code=fund_code,
                    fund_name=fund_name,
                    fund_type=fund_type,
                )
                uow.fund_favorites.add(favorite)
            else:
                favorite.fund_name = fund_name
                favorite.fund_type = fund_type

            await uow.commit()
            await uow.fund_favorites.refresh(favorite)
            return _to_item(favorite)

    async def list_favorite_funds(
        self,
        user: CurrentUser,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResponse[FavoriteFundItem]:
        async with self._uow_factory() as uow:
            total = await uow.fund_favorites.count_for_user(user.id, keyword)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            favorites = await uow.fund_favorites.list_for_user(
                user.id, keyword=keyword, offset=offset, limit=page_size
            )
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_item(favorite) for favorite in favorites],
            )

    async def list_favorite_fund_options(
        self, user: CurrentUser
    ) -> list[FavoriteFundOptionItem]:
        async with self._uow_factory() as uow:
            favorites = await uow.fund_favorites.list_options_for_user(user.id)
            return [_to_option_item(favorite) for favorite in favorites]

    async def list_favorite_fund_estimations(
        self,
        user: CurrentUser,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResponse[FavoriteFundEstimationItem]:
        favorite_page = await self.list_favorite_funds(
            user, keyword=keyword, page=page, page_size=page_size
        )
        estimations = _load_favorite_estimations(favorite_page.items, self._fund_query)
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

    async def get_favorite_fund_report(
        self,
        user: CurrentUser,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FavoriteFundReportResponse:
        favorite_page = await self.list_favorite_fund_estimations(
            user, keyword=keyword, page=page, page_size=page_size
        )
        items = favorite_page.items
        alerts = _build_alerts(items)
        estimated_items = [item for item in items if item.has_estimation]
        up_items = [
            item
            for item in estimated_items
            if _parse_percent(item.estimated_growth_rate) > 0
        ]
        down_items = [
            item
            for item in estimated_items
            if _parse_percent(item.estimated_growth_rate) < 0
        ]
        flat_items = [
            item
            for item in estimated_items
            if _parse_percent(item.estimated_growth_rate) == 0
        ]

        summary = FavoriteFundReportSummary(
            total=favorite_page.total,
            estimated_count=len(estimated_items),
            up_count=len(up_items),
            down_count=len(down_items),
            flat_count=len(flat_items),
            missing_count=len(items) - len(estimated_items),
            alert_count=len(alerts),
            max_up=_build_extreme(
                max(
                    up_items,
                    key=lambda item: _parse_percent(item.estimated_growth_rate),
                    default=None,
                )
            ),
            max_down=_build_extreme(
                min(
                    down_items,
                    key=lambda item: _parse_percent(item.estimated_growth_rate),
                    default=None,
                )
            ),
        )
        return FavoriteFundReportResponse(
            summary=summary, alerts=alerts, page=favorite_page
        )

    async def check_favorite_fund(
        self, user: CurrentUser, fund_code: str
    ) -> FavoriteFundCheckResponse:
        normalized_code = fund_code.strip()
        async with self._uow_factory() as uow:
            return FavoriteFundCheckResponse(
                favorited=await uow.fund_favorites.exists_for_user(
                    user.id, normalized_code
                )
            )

    async def remove_favorite_fund(
        self, user: CurrentUser, fund_code: str
    ) -> FavoriteFundRemoveResponse:
        normalized_code = fund_code.strip()
        async with self._uow_factory() as uow:
            removed_count = await uow.fund_favorites.remove_for_user(
                user.id, normalized_code
            )
            await uow.commit()
            return FavoriteFundRemoveResponse(removed=removed_count > 0)


def _to_current_user(user: User | CurrentUser) -> CurrentUser:
    if isinstance(user, CurrentUser):
        return user
    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
    )


def _service_from_session(db: AsyncSession) -> FundFavoriteService:
    return FundFavoriteService(lambda: FundUnitOfWork(lambda: db))


async def add_favorite_fund(
    db: AsyncSession, user: User | CurrentUser, payload: FavoriteFundAddRequest
) -> FavoriteFundItem:
    return await _service_from_session(db).add_favorite_fund(
        _to_current_user(user), payload
    )


async def list_favorite_funds(
    db: AsyncSession,
    user: User | CurrentUser,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[FavoriteFundItem]:
    return await _service_from_session(db).list_favorite_funds(
        _to_current_user(user), keyword=keyword, page=page, page_size=page_size
    )


async def list_favorite_fund_options(
    db: AsyncSession, user: User | CurrentUser
) -> list[FavoriteFundOptionItem]:
    return await _service_from_session(db).list_favorite_fund_options(
        _to_current_user(user)
    )


async def list_favorite_fund_estimations(
    db: AsyncSession,
    user: User | CurrentUser,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[FavoriteFundEstimationItem]:
    return await _service_from_session(db).list_favorite_fund_estimations(
        _to_current_user(user), keyword=keyword, page=page, page_size=page_size
    )


async def get_favorite_fund_report(
    db: AsyncSession,
    user: User | CurrentUser,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> FavoriteFundReportResponse:
    return await _service_from_session(db).get_favorite_fund_report(
        _to_current_user(user), keyword=keyword, page=page, page_size=page_size
    )


async def check_favorite_fund(
    db: AsyncSession, user: User | CurrentUser, fund_code: str
) -> FavoriteFundCheckResponse:
    return await _service_from_session(db).check_favorite_fund(
        _to_current_user(user), fund_code
    )


async def remove_favorite_fund(
    db: AsyncSession, user: User | CurrentUser, fund_code: str
) -> FavoriteFundRemoveResponse:
    return await _service_from_session(db).remove_favorite_fund(
        _to_current_user(user), fund_code
    )


def _load_favorite_estimations(
    favorites: list[FavoriteFundItem],
    fund_query: FundQueryFacade,
) -> dict[str, object]:
    if not favorites:
        return {}

    max_workers = min(8, len(favorites))
    estimations: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_by_code = {
            executor.submit(
                fund_query.find_fund_realtime_estimation, favorite.fund_code
            ): favorite.fund_code
            for favorite in favorites
        }
        for future in as_completed(future_by_code):
            fund_code = future_by_code[future]
            try:
                estimation = future.result()
            except Exception:
                estimation = None
            if estimation is not None:
                estimations[fund_code] = estimation
    return estimations


def _to_item(favorite) -> FavoriteFundItem:
    return FavoriteFundItem(
        id=favorite.id,
        fund_code=favorite.fund_code,
        fund_name=favorite.fund_name,
        fund_type=favorite.fund_type,
        created_at=favorite.created_at.isoformat(),
    )


def _to_option_item(favorite) -> FavoriteFundOptionItem:
    return FavoriteFundOptionItem(
        fund_code=favorite.fund_code,
        fund_name=favorite.fund_name,
        fund_type=favorite.fund_type,
    )


def _to_estimation_item(
    favorite: FavoriteFundItem, estimation
) -> FavoriteFundEstimationItem:
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


def _build_alerts(
    items: list[FavoriteFundEstimationItem],
) -> list[FavoriteFundAlertItem]:
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


def _build_extreme(
    item: FavoriteFundEstimationItem | None,
) -> FavoriteFundReportExtreme | None:
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
