from typing import Literal

from pydantic import BaseModel, Field


class FundSearchRequest(BaseModel):
    keyword: str | None = Field(default=None, description="基金代码、简称或拼音关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")


class FavoriteFundSearchRequest(BaseModel):
    keyword: str | None = Field(default=None, description="基金代码、名称或类型关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")


class FundEstimationSearchRequest(BaseModel):
    keyword: str | None = Field(default=None, description="基金代码或基金名称关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")
    category: str = Field(default="全部", description="基金分类")


class FundRankSearchRequest(BaseModel):
    category: str = Field(default="全部", description="基金分类")
    keyword: str | None = Field(default=None, description="基金代码或基金名称关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")


class FundSymbolRequest(BaseModel):
    symbol: str = Field(description="基金代码")


class FavoriteFundCodeRequest(BaseModel):
    fund_code: str = Field(description="基金代码")


class FavoriteFundAddRequest(BaseModel):
    fund_code: str = Field(description="基金代码")
    fund_name: str = Field(description="基金名称")
    fund_type: str | None = Field(default=None, description="基金类型")


class FundProfileRequest(BaseModel):
    symbol: str = Field(description="基金代码")
    year: str = Field(default="2024", description="查询年份")


class FundItem(BaseModel):
    code: str = Field(description="基金代码")
    abbreviation: str = Field(description="拼音缩写")
    name: str = Field(description="基金简称")
    fund_type: str = Field(description="基金类型")
    pinyin: str = Field(description="拼音全称")


class FavoriteFundItem(BaseModel):
    id: int
    fund_code: str
    fund_name: str
    fund_type: str | None
    created_at: str


class FavoriteFundEstimationItem(FavoriteFundItem):
    estimate_date: str | None
    estimated_nav: str | None
    estimated_growth_rate: str | None
    published_date: str | None
    published_nav: str | None
    published_growth_rate: str | None
    estimate_deviation: str | None
    previous_nav_date: str | None
    previous_nav: str | None
    has_estimation: bool


class FavoriteFundCheckResponse(BaseModel):
    favorited: bool


class FavoriteFundRemoveResponse(BaseModel):
    removed: bool


class FundEstimationItem(BaseModel):
    code: str = Field(description="基金代码")
    name: str = Field(description="基金名称")
    estimate_date: str = Field(description="估算日期")
    estimated_nav: str = Field(description="估算净值")
    estimated_growth_rate: str = Field(description="估算增长率")
    published_date: str = Field(description="公布数据日期")
    published_nav: str = Field(description="公布单位净值")
    published_growth_rate: str = Field(description="公布日增长率")
    estimate_deviation: str = Field(description="估算偏差")
    previous_nav_date: str = Field(description="上一交易日净值日期")
    previous_nav: str = Field(description="上一交易日单位净值")


class FundRankItem(BaseModel):
    code: str = Field(description="基金代码")
    name: str = Field(description="基金简称")
    fund_type: str = Field(description="基金类型")
    unit_nav: str = Field(description="单位净值")
    accumulated_nav: str = Field(description="累计净值")
    daily_growth_rate: str = Field(description="日增长率")
    weekly_growth_rate: str = Field(description="近1周")
    monthly_growth_rate: str = Field(description="近1月")
    quarterly_growth_rate: str = Field(description="近3月")
    half_year_growth_rate: str = Field(description="近6月")
    yearly_growth_rate: str = Field(description="近1年")
    current_year_growth_rate: str = Field(description="今年来")
    since_inception_growth_rate: str = Field(description="成立来")
    fee: str = Field(description="手续费")


class FundLatestNavItem(BaseModel):
    code: str = Field(description="基金代码")
    name: str = Field(description="基金简称")
    nav_date: str = Field(description="净值日期")
    unit_nav: str = Field(description="单位净值")
    accumulated_nav: str = Field(description="累计净值")
    daily_growth_value: str = Field(description="日增长值")
    daily_growth_rate: str = Field(description="日增长率")
    subscription_status: str = Field(description="申购状态")
    redemption_status: str = Field(description="赎回状态")
    fee: str = Field(description="手续费")


class FundValueRequest(BaseModel):
    fund_code: str = Field(description="基金编号")
    source: Literal["auto", "estimation", "daily"] = Field(default="auto", description="查询来源")


class FundValueResponse(BaseModel):
    fund_code: str
    source: Literal["estimation", "daily"]
    estimation: FundEstimationItem | None
    latest_nav: FundLatestNavItem | None


class FundDetailItem(BaseModel):
    item: str
    value: str


class FundDetailResponse(BaseModel):
    symbol: str
    items: list[FundDetailItem]


class FundFeeSection(BaseModel):
    title: str
    rows: list[dict[str, str]]


class FundProfileResponse(BaseModel):
    symbol: str
    year: str
    basic_info: list[FundDetailItem]
    fee_sections: list[FundFeeSection]
    holdings: list[dict[str, str]]
    industry_allocations: list[dict[str, str]]
