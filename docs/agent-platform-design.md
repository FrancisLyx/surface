# 金融智能体平台 MVP 设计文档

## 1. 背景

当前项目已经具备用户登录、基金列表、我的自选、AI 基金分析、流式输出和报告保存能力。现有 AI 功能是单一链路：前端传基金代码，后端拼接 Prompt，调用大模型流式返回并保存报告。

下一阶段目标是把单一 AI 页面升级为“金融智能体平台”，用于统一管理不同类型的金融分析智能体、运行记录和分析报告。

## 2. 产品定位

第一版不做通用无边界 Agent 平台，而是做：

> 面向个人投资研究的金融智能体平台。

平台核心能力：

- 管理系统内置金融智能体。
- 运行固定 LangGraph 分析流程。
- 调用已有基金数据工具。
- 流式生成 Markdown 报告。
- 保存用户维度的运行记录和报告。
- 前端提供智能体列表、运行页、报告中心。

## 3. 第一版范围

### 3.1 包含内容

第一版内置两个智能体：

1. **基金深度分析**
   - 输入：基金代码。
   - 数据：基金画像、实时估值、历史净值摘要、持仓、行业配置。
   - 输出：单基金 Markdown 投研报告。

2. **自选基金扫描**
   - 输入：可选分页条数。
   - 数据：当前登录用户的自选基金估值和提醒数据。
   - 输出：自选组合扫描报告。

平台能力：

- 查询可用智能体。
- 流式运行智能体。
- 保存运行记录。
- 保存分析报告。
- 查询报告列表。
- 查询报告详情。

### 3.2 暂不包含内容

第一版不做：

- 可视化拖拽编排。
- 用户自定义 Python 工具。
- 用户自定义 Agent 工作流。
- 多 Agent 自动协作。
- 计费和调用成本统计。
- RAG 知识库。
- 新闻情绪分析。
- 股票、指数、宏观全市场分析。

这些能力可以后续迭代。

## 4. 后端架构

推荐目录结构：

```text
app/
  agents/
    fund_analysis_graph.py

  tools/
    fund_tools.py

  services/
    agent_service.py
    agent_runtime_service.py

  api/routes/agent/
    agent_schema.py
    agent_view.py

  db/models/
    agent.py

  sql/
    006_create_agent_platform.sql
```

职责说明：

- `app/clients/langchain_client.py`
  - 继续只负责创建 LangChain 模型和流式调用。

- `app/agents/fund_analysis_graph.py`
  - 定义 LangGraph 固定流程。
  - 第一版包含 `fund_deep_analysis_graph` 和 `favorite_fund_scan_graph`。

- `app/tools/fund_tools.py`
  - 封装基金数据工具。
  - 调用现有 `fund_service` 和 `fund_favorite_service`。

- `app/services/agent_service.py`
  - 负责智能体定义、运行记录、报告保存、报告查询。

- `app/services/agent_runtime_service.py`
  - 根据 `graph_code` 调用对应 LangGraph。

- `app/api/routes/agent`
  - 暴露 `/api/v1/agents/*` 接口。

## 5. LangGraph 流程设计

### 5.1 基金深度分析 Graph

```text
start
  ↓
load_fund_data
  ↓
build_prompt
  ↓
stream_llm
  ↓
save_run_and_report
  ↓
end
```

说明：

- `load_fund_data` 获取基金画像、估值、行业配置、持仓、近一年净值摘要。
- `build_prompt` 生成专业金融分析 Prompt。
- `stream_llm` 使用 LangChain 流式调用 DeepSeek。
- `save_run_and_report` 保存运行记录和报告。

### 5.2 自选基金扫描 Graph

```text
start
  ↓
load_favorite_data
  ↓
build_prompt
  ↓
stream_llm
  ↓
save_run_and_report
  ↓
end
```

说明：

- `load_favorite_data` 获取当前用户自选基金估值和提醒数据。
- 输出偏向组合扫描、异常提醒、收盘前操作建议。

## 6. 数据库设计

### 6.1 agent_definitions

保存智能体定义。

```sql
agent_definitions
- id
- name
- code
- agent_type
- description
- system_prompt
- graph_code
- enabled
- is_builtin
- owner_user_id
- created_at
- updated_at
```

用途：

- 平台展示可用智能体。
- 后端根据 `graph_code` 决定运行哪个 LangGraph。
- 第一版只启用系统内置 Agent。

### 6.2 agent_runs

保存每次运行记录。

```sql
agent_runs
- id
- user_id
- agent_id
- input_json
- output_text
- status
- error_message
- duration_ms
- created_at
- finished_at
```

用途：

- 记录用户每次调用。
- 后续可扩展运行日志、耗时统计、失败重试。

### 6.3 agent_reports

保存最终报告。

```sql
agent_reports
- id
- user_id
- agent_id
- run_id
- title
- target_type
- target_code
- content
- created_at
```

用途：

- 替代长期依赖 `ai_fund_reports` 的单一报告表。
- 支持多 Agent、多类型报告。

说明：

- 旧表 `ai_fund_reports` 第一阶段可以保留，避免影响现有 AI 页面。
- 新平台页面使用 `agent_reports`。

## 7. 后端接口设计

### 7.1 查询智能体列表

```http
POST /api/v1/agents/list
```

请求：

```json
{
  "page": 1,
  "page_size": 20
}
```

响应：

```json
{
  "items": [
    {
      "id": 1,
      "name": "基金深度分析",
      "code": "fund_deep_analysis",
      "agent_type": "fund",
      "description": "基于基金画像、实时估值、持仓与近一年净值走势生成单基金投研报告。",
      "graph_code": "fund_deep_analysis_graph",
      "enabled": true,
      "is_builtin": true
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2,
  "pages": 1
}
```

### 7.2 流式运行智能体

```http
POST /api/v1/agents/run/stream
```

请求：

```json
{
  "agent_code": "fund_deep_analysis",
  "input": {
    "fund_code": "110010"
  }
}
```

返回：

```text
text/event-stream
```

事件：

```text
data: markdown chunk

event: done
data: [DONE]
```

### 7.3 查询报告列表

```http
POST /api/v1/agents/reports/list
```

请求：

```json
{
  "agent_code": "fund_deep_analysis",
  "target_code": "110010",
  "page": 1,
  "page_size": 10
}
```

### 7.4 查询报告详情

```http
POST /api/v1/agents/reports/detail
```

请求：

```json
{
  "id": 1
}
```

## 8. 前端页面设计

### 8.1 菜单建议

保留当前核心菜单，同时新增：

```text
基金列表
我的自选
智能体
报告中心
系统设置
```

现有“自选分析”可以先保留，也可以后续迁移到“智能体”。

### 8.2 智能体列表页

路径：

```text
/agents
```

展示内容：

- 智能体名称。
- 类型。
- 描述。
- 是否内置。
- 运行按钮。

点击运行进入：

```text
/agents/run/:agentCode
```

### 8.3 智能体运行页

路径：

```text
/agents/run/:agentCode
```

不同 Agent 使用不同表单：

- `fund_deep_analysis`
  - 自选基金选择。
  - 基金代码输入。

- `favorite_fund_scan`
  - 扫描数量。

输出区域：

- 使用现有 `CherryMarkdownViewer`。
- 支持流式输出。
- 支持停止生成。
- 完成后刷新报告列表。

### 8.4 报告中心

路径：

```text
/agent-reports
```

展示内容：

- 报告标题。
- 智能体名称。
- 分析对象。
- 生成时间。
- 查看详情。

详情展示：

- Markdown 报告内容。

## 9. 鉴权和数据隔离

所有 `/api/v1/agents/*` 接口都需要 JWT 鉴权。

数据隔离规则：

- 用户只能查看自己的 `agent_runs`。
- 用户只能查看自己的 `agent_reports`。
- 系统内置 Agent 所有人可见。
- 用户自定义 Agent 第一版不开放。

## 10. 风险控制

金融分析输出必须遵守：

- 不承诺收益。
- 不输出“必涨”“稳赚”“必须买入”等确定性建议。
- 数据缺失必须明确说明。
- 估算日期与公布日期不一致时，不能直接比较。
- 报告必须包含免责声明：
  - “以上内容仅用于学习和信息分析，不构成投资建议。”

## 11. 测试计划

后端测试：

- 查询智能体列表返回两个内置 Agent。
- 流式运行 Agent 后保存 `agent_runs` 和 `agent_reports`。
- 报告列表和详情按用户隔离。
- 未登录访问返回 401。

前端验证：

- `npm run lint`
- `npm run build`
- 登录后能看到智能体菜单。
- 能选择基金生成流式报告。
- 报告中心能查看历史报告。

## 12. 推荐迭代顺序

第一阶段：

1. 后端 Agent 表、SQL、模型。
2. 后端 Agent 列表、流式运行、报告接口。
3. 前端智能体列表、运行页、报告中心。
4. 保留旧 AI 基金分析页面。

第二阶段：

1. 把旧 AI 基金分析迁移到 Agent 平台。
2. 增加 Agent 启用/关闭设置。
3. 增加运行失败日志和重试。

第三阶段：

1. 扩展市场分析 Agent。
2. 扩展基金对比 Agent。
3. 引入新闻、指数、宏观数据。

