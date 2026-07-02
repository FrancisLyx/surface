from pydantic import BaseModel, Field


class AiFundSummaryRequest(BaseModel):
    fund_code: str = Field(description="基金代码")


class AiFundReportListRequest(BaseModel):
    fund_code: str | None = Field(default=None, description="基金代码")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")


class AiFundReportDetailRequest(BaseModel):
    id: int = Field(description="报告 ID")


class AiFundReportListItem(BaseModel):
    id: int
    fund_code: str
    created_at: str


class AiFundReportDetailResponse(AiFundReportListItem):
    content: str
