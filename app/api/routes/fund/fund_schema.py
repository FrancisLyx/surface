from typing import Literal

from pydantic import BaseModel, Field


class FundSearchRequest(BaseModel):
    keyword: str | None = Field(default=None, description="基金代码、简称或拼音关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")


class FundEstimationSearchRequest(BaseModel):
    keyword: str | None = Field(default=None, description="基金代码或基金名称关键字")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=200, description="每页条数")
    category: str = Field(default="全部", description="基金分类")


class FundSymbolRequest(BaseModel):
    symbol: str = Field(description="基金代码")


class FundItem(BaseModel):
    code: str = Field(description="基金代码")
    abbreviation: str = Field(description="拼音缩写")
    name: str = Field(description="基金简称")
    fund_type: str = Field(description="基金类型")
    pinyin: str = Field(description="拼音全称")


class FundEstimationItem(BaseModel):
    code: str = Field(description="基金代码")
    name: str = Field(description="基金名称")
    estimate_date: str = Field(description="估算日期")
    estimated_nav: str = Field(description="估算净值")
    estimated_growth_rate: str = Field(description="估算增长率")
    published_nav: str = Field(description="公布单位净值")
    published_growth_rate: str = Field(description="公布日增长率")
    estimate_deviation: str = Field(description="估算偏差")
    previous_nav_date: str = Field(description="上一交易日净值日期")
    previous_nav: str = Field(description="上一交易日单位净值")


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
