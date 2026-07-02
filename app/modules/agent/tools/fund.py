from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fund.public import FundQueryFacade
from app.modules.fund.schemas import FundProfileRequest, FundValueRequest


def load_fund_analysis_data(fund_code: str) -> dict[str, object]:
    normalized_code = fund_code.strip()
    fund_query = FundQueryFacade()
    fund_value = fund_query.get_fund_value(
        FundValueRequest(fund_code=normalized_code, source="auto")
    )
    profile = fund_query.get_fund_profile(
        FundProfileRequest(symbol=normalized_code, year=str(date.today().year))
    )
    nav_trend_summary = fund_query.get_fund_nav_trend_summary(normalized_code)

    return {
        "fund_code": normalized_code,
        "fund_value": fund_value,
        "profile": profile,
        "nav_trend_summary": nav_trend_summary,
    }


def load_favorite_scan_data(
    db: AsyncSession | None, user: object | None, page_size: int = 20
) -> dict[str, object]:
    if db is None:
        return {"favorite_report": None}
    return {
        "favorite_report": {
            "message": "favorite scan data must be loaded by the async application service before graph execution",
            "page_size": page_size,
        }
    }
