from fastapi import HTTPException

from app.api.routes.fund.fund_schema import (
    FundDetailItem,
    FundDetailResponse,
    FundEstimationItem,
    FundItem,
    FundLatestNavItem,
    FundValueRequest,
    FundValueResponse,
)
from app.clients import akshare_client
from app.core.pagination import PageResponse, paginate


def list_funds(keyword: str | None = None, page: int = 1, page_size: int = 20) -> PageResponse[FundItem]:
    try:
        fund_df = akshare_client.get_fund_names()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AkShare fund query failed: {exc}") from exc

    normalized_keyword = keyword.strip().lower() if keyword else None
    items: list[FundItem] = []

    for _, row in fund_df.iterrows():
        code = str(row.get("基金代码", ""))
        abbreviation = str(row.get("拼音缩写", ""))
        name = str(row.get("基金简称", ""))
        fund_type = str(row.get("基金类型", ""))
        pinyin = str(row.get("拼音全称", ""))

        searchable_text = f"{code} {abbreviation} {name} {fund_type} {pinyin}".lower()
        if normalized_keyword and normalized_keyword not in searchable_text:
            continue

        items.append(
            FundItem(
                code=code,
                abbreviation=abbreviation,
                name=name,
                fund_type=fund_type,
                pinyin=pinyin,
            )
        )

    return paginate(items, page=page, page_size=page_size)


def list_fund_estimations(
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    category: str = "全部",
) -> PageResponse[FundEstimationItem]:
    estimation_df = _load_fund_estimations(category)
    normalized_keyword = keyword.strip().lower() if keyword else None
    items: list[FundEstimationItem] = []

    for _, row in estimation_df.iterrows():
        item = _build_fund_estimation_item(row, estimation_df.columns)
        searchable_text = f"{item.code} {item.name}".lower()
        if normalized_keyword and normalized_keyword not in searchable_text:
            continue

        items.append(item)

    return paginate(items, page=page, page_size=page_size)


def get_fund_value(request: FundValueRequest) -> FundValueResponse:
    fund_code = request.fund_code.strip()
    if not fund_code:
        raise HTTPException(status_code=400, detail="fund_code is required")

    if request.source in {"auto", "estimation"}:
        estimation = find_fund_estimation(fund_code)
        if estimation is not None:
            return FundValueResponse(
                fund_code=fund_code,
                source="estimation",
                estimation=estimation,
                latest_nav=None,
            )
        if request.source == "estimation":
            raise HTTPException(status_code=404, detail=f"Fund estimation not found: {fund_code}")

    latest_nav = find_fund_latest_nav(fund_code)
    if latest_nav is not None:
        return FundValueResponse(
            fund_code=fund_code,
            source="daily",
            estimation=None,
            latest_nav=latest_nav,
        )

    raise HTTPException(status_code=404, detail=f"Fund value not found: {fund_code}")


def get_fund_estimation(symbol: str) -> FundEstimationItem:
    item = find_fund_estimation(symbol)
    if item is not None:
        return item
    raise HTTPException(status_code=404, detail=f"Fund estimation not found: {symbol}")


def get_fund_detail(symbol: str) -> FundDetailResponse:
    try:
        detail_df = akshare_client.get_fund_detail(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AkShare fund detail query failed: {exc}") from exc

    items = [
        FundDetailItem(item=str(row.get("item", "")), value=str(row.get("value", "")))
        for _, row in detail_df.iterrows()
    ]
    return FundDetailResponse(symbol=symbol, items=items)


def find_fund_estimation(fund_code: str) -> FundEstimationItem | None:
    estimation_df = _load_fund_estimations("全部")
    for _, row in estimation_df.iterrows():
        item = _build_fund_estimation_item(row, estimation_df.columns)
        if item.code == fund_code:
            return item
    return None


def find_fund_latest_nav(fund_code: str) -> FundLatestNavItem | None:
    daily_df = _load_open_fund_daily()
    for _, row in daily_df.iterrows():
        item = _build_fund_latest_nav_item(row, daily_df.columns)
        if item.code == fund_code:
            return item
    return None


def _load_fund_estimations(category: str):
    try:
        return akshare_client.get_fund_estimations(category)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AkShare fund estimation query failed: {exc}") from exc


def _load_open_fund_daily():
    try:
        return akshare_client.get_open_fund_daily()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AkShare fund daily nav query failed: {exc}") from exc


def _build_fund_estimation_item(row, columns) -> FundEstimationItem:
    estimated_nav_column = _find_column(columns, "估算数据-估算值")
    estimated_growth_column = _find_column(columns, "估算数据-估算增长率")
    published_nav_column = _find_column(columns, "公布数据-单位净值")
    published_growth_column = _find_column(columns, "公布数据-日增长率")
    previous_nav_column = _find_column(columns, "单位净值", exclude="公布数据")

    return FundEstimationItem(
        code=str(row.get("基金代码", "")),
        name=str(row.get("基金名称", "")),
        estimate_date=_extract_date(estimated_nav_column),
        estimated_nav=str(row.get(estimated_nav_column, "")),
        estimated_growth_rate=str(row.get(estimated_growth_column, "")),
        published_nav=str(row.get(published_nav_column, "")),
        published_growth_rate=str(row.get(published_growth_column, "")),
        estimate_deviation=str(row.get("估算偏差", "")),
        previous_nav_date=_extract_date(previous_nav_column),
        previous_nav=str(row.get(previous_nav_column, "")),
    )


def _build_fund_latest_nav_item(row, columns) -> FundLatestNavItem:
    unit_nav_column = _find_latest_nav_column(row, columns, "单位净值")
    unit_nav_date = _extract_date(unit_nav_column)
    accumulated_nav_column = _find_nav_column_by_date(columns, "累计净值", unit_nav_date)

    return FundLatestNavItem(
        code=str(row.get("基金代码", "")),
        name=str(row.get("基金简称", "")),
        nav_date=_extract_date(unit_nav_column),
        unit_nav=str(row.get(unit_nav_column, "")),
        accumulated_nav=str(row.get(accumulated_nav_column, "")),
        daily_growth_value=str(row.get("日增长值", "")),
        daily_growth_rate=str(row.get("日增长率", "")),
        subscription_status=str(row.get("申购状态", "")),
        redemption_status=str(row.get("赎回状态", "")),
        fee=str(row.get("手续费", "")),
    )


def _find_column(columns, include: str, exclude: str | None = None) -> str:
    for column in columns:
        column_name = str(column)
        if include in column_name and (exclude is None or exclude not in column_name):
            return column_name
    return ""


def _find_latest_nav_column(row, columns, include: str) -> str:
    matching_columns = [str(column) for column in columns if include in str(column)]
    for column in matching_columns:
        if str(column).split("-")[-1] == include and _extract_date(column):
            value = str(row.get(column, ""))
            if value and value != "---":
                return column
    return matching_columns[-1] if matching_columns else ""


def _find_nav_column_by_date(columns, include: str, value_date: str) -> str:
    for column in columns:
        column_name = str(column)
        if include in column_name and value_date and _extract_date(column_name) == value_date:
            return column_name
    return _find_column(columns, include)


def _extract_date(column_name: str) -> str:
    parts = column_name.split("-")
    if len(parts) >= 3 and all(part.isdigit() for part in parts[:3]):
        return "-".join(parts[:3])
    return ""
