from pydantic import BaseModel, Field


class AgentListRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class AgentChatStreamRequest(BaseModel):
    agent_id: int = Field(description="智能体 ID")
    message: str = Field(min_length=1, description="用户消息")
    conversation_id: int | None = Field(default=None, description="会话 ID")
    fund_code: str | None = Field(default=None, description="基金代码")


class AgentReportListRequest(BaseModel):
    agent_id: int | None = Field(default=None, description="智能体 ID")
    target_code: str | None = Field(default=None, description="分析对象编码")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")


class AgentReportDetailRequest(BaseModel):
    id: int = Field(description="报告 ID")


class AgentConversationListRequest(BaseModel):
    agent_id: int = Field(description="智能体 ID")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")


class AgentConversationDetailRequest(BaseModel):
    conversation_id: int = Field(description="会话 ID")


class AgentListItem(BaseModel):
    id: int
    name: str
    agent_type: str
    description: str
    enabled: bool
    is_builtin: bool


class AgentReportListItem(BaseModel):
    id: int
    agent_id: int
    agent_name: str
    run_id: int
    title: str
    target_type: str
    target_code: str | None
    created_at: str


class AgentReportDetailResponse(AgentReportListItem):
    content: str


class AgentConversationListItem(BaseModel):
    id: int
    agent_id: int
    title: str
    target_type: str | None
    target_code: str | None
    created_at: str
    updated_at: str


class AgentConversationMessageItem(BaseModel):
    id: int
    role: str
    message_type: str
    content: str
    created_at: str


class AgentConversationDetailResponse(BaseModel):
    id: int
    agent_id: int
    title: str
    target_type: str | None
    target_code: str | None
    messages: list[AgentConversationMessageItem]
