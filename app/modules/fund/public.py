from app.modules.fund import service as fund_service
from app.modules.fund.schemas import (
    FundEstimationItem,
    FundLatestNavItem,
    FundProfileRequest,
    FundProfileResponse,
    FundValueRequest,
    FundValueResponse,
)


class FundQueryFacade:
    def get_fund_value(self, request: FundValueRequest) -> FundValueResponse:
        return fund_service.get_fund_value(request)

    def get_fund_profile(self, request: FundProfileRequest) -> FundProfileResponse:
        return fund_service.get_fund_profile(request)

    def get_fund_nav_trend_summary(self, symbol: str) -> dict[str, object]:
        return fund_service.get_fund_nav_trend_summary(symbol)

    def find_fund_realtime_estimation(
        self, fund_code: str
    ) -> FundEstimationItem | None:
        return fund_service.find_fund_realtime_estimation(fund_code)

    def find_fund_estimation(self, fund_code: str) -> FundEstimationItem | None:
        return fund_service.find_fund_estimation(fund_code)

    def find_fund_latest_nav(self, fund_code: str) -> FundLatestNavItem | None:
        return fund_service.find_fund_latest_nav(fund_code)


def get_fund_value(request: FundValueRequest) -> FundValueResponse:
    return FundQueryFacade().get_fund_value(request)


def get_fund_profile(request: FundProfileRequest) -> FundProfileResponse:
    return FundQueryFacade().get_fund_profile(request)


def get_fund_nav_trend_summary(symbol: str) -> dict[str, object]:
    return FundQueryFacade().get_fund_nav_trend_summary(symbol)


def find_fund_realtime_estimation(fund_code: str) -> FundEstimationItem | None:
    return FundQueryFacade().find_fund_realtime_estimation(fund_code)
