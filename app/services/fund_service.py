from fastapi import HTTPException
from datetime import date, datetime, timedelta

from app.api.routes.fund.fund_schema import (
    FundDetailItem,
    FundDetailResponse,
    FundEstimationItem,
    FundFeeSection,
    FundItem,
    FundLatestNavItem,
    FundProfileRequest,
    FundProfileResponse,
    FundRankItem,
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
    items = list_all_fund_estimations(category)
    normalized_keyword = keyword.strip().lower() if keyword else None
    filtered_items: list[FundEstimationItem] = []

    for item in items:
        searchable_text = f"{item.code} {item.name}".lower()
        if normalized_keyword and normalized_keyword not in searchable_text:
            continue

        filtered_items.append(item)

    return paginate(filtered_items, page=page, page_size=page_size)


def list_all_fund_estimations(category: str = "全部") -> list[FundEstimationItem]:
    estimation_df = _load_fund_estimations(category)
    return [
        _build_fund_estimation_item(row, estimation_df.columns)
        for _, row in estimation_df.iterrows()
    ]


def list_fund_rank(
    category: str = "全部",
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[FundRankItem]:
    try:
        rank_df = akshare_client.get_open_fund_rank(category)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AkShare fund rank query failed: {exc}") from exc

    normalized_keyword = keyword.strip().lower() if keyword else None
    items: list[FundRankItem] = []

    for _, row in rank_df.iterrows():
        item = _build_fund_rank_item(row)
        searchable_text = f"{item.code} {item.name} {item.fund_type}".lower()
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


def get_fund_profile(request: FundProfileRequest) -> FundProfileResponse:
    symbol = request.symbol.strip()
    year = request.year.strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    if not year:
        raise HTTPException(status_code=400, detail="year is required")

    basic_info = get_fund_detail(symbol).items

    return FundProfileResponse(
        symbol=symbol,
        year=year,
        basic_info=basic_info,
        fee_sections=_load_profile_fee_sections(symbol),
        holdings=_load_profile_rows(
            lambda: akshare_client.get_fund_portfolio_hold(symbol, year),
        ),
        industry_allocations=_load_profile_rows(
            lambda: akshare_client.get_fund_industry_allocation(symbol, year),
        ),
    )


def get_fund_nav_trend_summary(symbol: str) -> dict[str, object]:
    try:
        nav_trend_df = akshare_client.get_fund_nav_trend(symbol)
    except Exception:
        return {
            "period": "近一年",
            "message": "近一年净值走势数据暂不可用",
            "latest_points": [],
        }

    points: list[dict[str, str]] = []
    for _, row in nav_trend_df.iterrows():
        nav_date = _parse_date_value(row.get("净值日期", row.get("日期", "")))
        unit_nav = _parse_float(row.get("单位净值", row.get("净值", "")))
        if nav_date is None or unit_nav is None:
            continue
        points.append(
            {
                "date": nav_date,
                "unit_nav": unit_nav,
                "raw": {
                    "净值日期": nav_date.isoformat(),
                    "单位净值": f"{unit_nav:.4f}",
                },
            }
        )

    points.sort(key=lambda item: item["date"])
    if not points:
        return {
            "period": "近一年",
            "message": "近一年净值走势数据为空",
            "latest_points": [],
        }

    end_date = points[-1]["date"]
    start_boundary = end_date - timedelta(days=365)
    recent_points = [point for point in points if point["date"] >= start_boundary]
    if not recent_points:
        recent_points = points[-min(len(points), 20) :]

    start_point = recent_points[0]
    end_point = recent_points[-1]
    start_nav = start_point["unit_nav"]
    end_nav = end_point["unit_nav"]
    period_return = ((end_nav - start_nav) / start_nav) * 100 if start_nav else 0

    peak = recent_points[0]["unit_nav"]
    max_drawdown = 0.0
    for point in recent_points:
        unit_nav = point["unit_nav"]
        if unit_nav > peak:
            peak = unit_nav
        if peak:
            drawdown = ((unit_nav - peak) / peak) * 100
            if drawdown < max_drawdown:
                max_drawdown = drawdown

    return {
        "period": "近一年",
        "start_date": start_point["date"].isoformat(),
        "end_date": end_point["date"].isoformat(),
        "start_nav": f"{start_nav:.4f}",
        "end_nav": f"{end_nav:.4f}",
        "period_return": f"{period_return:.2f}%",
        "max_drawdown": f"{max_drawdown:.2f}%",
        "latest_points": [point["raw"] for point in recent_points[-10:]],
    }


def find_fund_estimation(fund_code: str) -> FundEstimationItem | None:
    realtime_item = find_fund_realtime_estimation(fund_code)
    if realtime_item is not None:
        return realtime_item

    estimation_df = _load_fund_estimations("全部")
    for _, row in estimation_df.iterrows():
        item = _build_fund_estimation_item(row, estimation_df.columns)
        if item.code == fund_code:
            return item
    return None


def find_fund_realtime_estimation(fund_code: str) -> FundEstimationItem | None:
    try:
        data = akshare_client.get_fund_realtime_estimation(fund_code)
    except Exception:
        return None

    code = str(data.get("fundcode", "")).strip()
    estimated_nav = str(data.get("gsz", "")).strip()
    if not code or not estimated_nav:
        return None

    estimate_time = str(data.get("gztime", "")).strip()
    estimate_date = estimate_time.split(" ")[0] if estimate_time else ""
    estimated_growth_rate = _format_rate(data.get("gszzl", ""))
    published_date = str(data.get("jzrq", "")).strip()

    return FundEstimationItem(
        code=code,
        name=str(data.get("name", "")).strip(),
        estimate_date=estimate_date,
        estimated_nav=estimated_nav,
        estimated_growth_rate=estimated_growth_rate,
        published_date=published_date,
        published_nav=str(data.get("dwjz", "")).strip(),
        published_growth_rate="",
        estimate_deviation="",
        previous_nav_date=published_date,
        previous_nav=str(data.get("dwjz", "")).strip(),
    )


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


def _build_fund_estimation_item(
    row,
    columns,
    latest_nav_by_code: dict[str, FundLatestNavItem] | None = None,
) -> FundEstimationItem:
    estimated_nav_column = _find_column(columns, "估算数据-估算值")
    estimated_growth_column = _find_column(columns, "估算数据-估算增长率")
    published_nav_column = _find_column(columns, "公布数据-单位净值")
    published_growth_column = _find_column(columns, "公布数据-日增长率")
    previous_nav_column = _find_column(columns, "单位净值", exclude="公布数据")
    code = str(row.get("基金代码", ""))
    estimate_date = _extract_date(estimated_nav_column)
    published_nav = str(row.get(published_nav_column, ""))
    published_growth_rate = str(row.get(published_growth_column, ""))
    published_date = _extract_date(published_nav_column)

    latest_nav = latest_nav_by_code.get(code) if latest_nav_by_code else None
    if latest_nav is not None and latest_nav.unit_nav:
        published_date = latest_nav.nav_date
        published_nav = latest_nav.unit_nav
        published_growth_rate = latest_nav.daily_growth_rate

    estimate_deviation = str(row.get("估算偏差", ""))

    return FundEstimationItem(
        code=code,
        name=str(row.get("基金名称", "")),
        estimate_date=estimate_date,
        estimated_nav=str(row.get(estimated_nav_column, "")),
        estimated_growth_rate=str(row.get(estimated_growth_column, "")),
        published_date=published_date,
        published_nav=published_nav,
        published_growth_rate=published_growth_rate,
        estimate_deviation=estimate_deviation if estimate_date == published_date else "",
        previous_nav_date=_extract_date(previous_nav_column),
        previous_nav=str(row.get(previous_nav_column, "")),
    )


def _load_latest_nav_index() -> dict[str, FundLatestNavItem]:
    try:
        daily_df = _load_open_fund_daily()
    except Exception:
        return {}

    latest_nav_by_code: dict[str, FundLatestNavItem] = {}
    for _, row in daily_df.iterrows():
        item = _build_fund_latest_nav_item(row, daily_df.columns)
        if item.code:
            latest_nav_by_code[item.code] = item
    return latest_nav_by_code




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


def _build_fund_rank_item(row) -> FundRankItem:
    return FundRankItem(
        code=str(row.get("基金代码", "")),
        name=str(row.get("基金简称", row.get("基金名称", ""))),
        fund_type=str(row.get("基金类型", "")),
        unit_nav=str(row.get("单位净值", "")),
        accumulated_nav=str(row.get("累计净值", "")),
        daily_growth_rate=str(row.get("日增长率", "")),
        weekly_growth_rate=str(row.get("近1周", "")),
        monthly_growth_rate=str(row.get("近1月", "")),
        quarterly_growth_rate=str(row.get("近3月", "")),
        half_year_growth_rate=str(row.get("近6月", "")),
        yearly_growth_rate=str(row.get("近1年", "")),
        current_year_growth_rate=str(row.get("今年来", "")),
        since_inception_growth_rate=str(row.get("成立来", "")),
        fee=str(row.get("手续费", "")),
    )


def _load_profile_fee_sections(symbol: str) -> list[FundFeeSection]:
    sections: list[FundFeeSection] = []
    for indicator in ["申购费率（前端）", "赎回费率", "运作费用"]:
        rows = _load_profile_rows(lambda indicator=indicator: akshare_client.get_fund_fee(symbol, indicator))
        sections.append(FundFeeSection(title=indicator, rows=rows))
    return sections


def _load_profile_rows(loader) -> list[dict[str, str]]:
    try:
        data_frame = loader()
    except Exception:
        return []

    rows: list[dict[str, str]] = []
    for _, row in data_frame.iterrows():
        rows.append({str(key): str(value) for key, value in _row_items(row)})
    return rows


def _row_items(row):
    if hasattr(row, "items"):
        return row.items()
    if isinstance(row, dict):
        return row.items()
    return []


def _parse_date_value(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    value_text = str(value).strip()
    if not value_text:
        return None
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value_text, date_format).date()
        except ValueError:
            continue
    return None


def _parse_float(value) -> float | None:
    value_text = str(value).strip().replace(",", "")
    if not value_text or value_text == "---":
        return None
    try:
        return float(value_text)
    except ValueError:
        return None


def _format_rate(value) -> str:
    value_text = str(value).strip()
    if not value_text:
        return ""
    if value_text.endswith("%"):
        return value_text
    return f"{value_text}%"


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
