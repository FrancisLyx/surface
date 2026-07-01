from datetime import date

from sqlalchemy.orm import Session

from app.api.routes.fund.fund_schema import FundProfileRequest, FundValueRequest
from app.db.models.user import User
from app.services import fund_favorite_service, fund_service


def load_fund_analysis_data(fund_code: str) -> dict[str, object]:
    normalized_code = fund_code.strip()
    fund_value = fund_service.get_fund_value(FundValueRequest(fund_code=normalized_code, source="auto"))
    profile = fund_service.get_fund_profile(FundProfileRequest(symbol=normalized_code, year=str(date.today().year)))
    nav_trend_summary = fund_service.get_fund_nav_trend_summary(normalized_code)

    return {
        "fund_code": normalized_code,
        "fund_value": fund_value,
        "profile": profile,
        "nav_trend_summary": nav_trend_summary,
    }


def load_favorite_scan_data(db: Session, user: User, page_size: int = 20) -> dict[str, object]:
    report = fund_favorite_service.get_favorite_fund_report(db, user, page=1, page_size=page_size)
    return {"favorite_report": report}
