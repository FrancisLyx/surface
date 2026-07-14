# fix: 固定 pandas 版本避免 AkShare 崩溃

## 需求理解
修复市场格局策略分析接口调用失败问题。前端通过 Vite 代理请求 `/api/v1/strategies/analyze` 时出现 `socket hang up`，根因是后端在调用 AkShare ETF 实时行情接口时触发 Python native 崩溃。

## 改动文件列表
- `pyproject.toml`：新增 `pandas<3` 依赖约束，避免解析到已知异常的 pandas 3.0.4。
- `uv.lock`：重新锁定 pandas 到 2.3.3，并移除 pandas 3.0.4 相关锁定条目。

## 关键实现说明
- 单独复现 `akshare.fund_etf_spot_em()`，确认 pandas 3.0.4 下执行完 AkShare 进度条后进程以退出码 138 崩溃。
- `uv lock` 曾提示 `pandas==3.0.4` 已被 yanked，原因是 datetime 相关 segfault。
- 通过显式增加 `pandas<3`，让 AkShare 依赖解析到 pandas 2.3.3，避开崩溃版本。
- 执行 `uv lock && uv sync` 后，本地环境从 pandas 3.0.4 降级到 2.3.3，并重启后端服务验证。

## 风险与兼容性影响
- 该约束会阻止项目安装 pandas 3.x，后续如需升级 pandas，需要先验证 AkShare 与相关行情接口兼容性。
- 当前项目直接使用 pandas 的业务代码较少，主要由 AkShare 传递依赖使用，兼容性风险较低。
- 锁文件更新会影响 CI 和部署环境的依赖解析，预期效果是统一使用 pandas 2.3.3。

## 验证步骤
- `uv run python` 直接调用 `ak.fund_etf_spot_em()`：pandas 2.3.3 下返回 1544 行 ETF 数据，不再崩溃。
- `curl http://127.0.0.1:8000/api/v1/health/live`：返回 200。
- 直连 `127.0.0.1:8000/api/v1/strategies/analyze`：返回 200。
- 经 Vite 代理 `localhost:5173/api/v1/strategies/analyze`：返回 200。
- `uv run pytest tests/test_strategy_routes.py tests/test_akshare_client.py`：17 passed，1 个 passlib/crypt Python 3.13 弃用警告。

## 前端测试建议
不涉及前端代码变更；建议在浏览器打开“策略分析 / 市场格局风向标”，确认页面首屏加载、刷新按钮和自动刷新不再出现 Vite proxy `socket hang up`。

## 代码审查建议
- 重点确认 `pandas<3` 约束是否符合当前 AkShare 版本兼容范围。
- 检查 `uv.lock` 是否已移除 pandas 3.0.4，且项目运行环境统一解析到 pandas 2.3.3。
- 关注后续依赖升级时是否重新引入 yanked 或 native crash 风险。

## 回滚建议
- 如后续 AkShare 或 pandas 修复了 3.x 兼容问题，可移除 `pandas<3` 并执行 `uv lock && uv sync` 后重新验证策略接口。
- 如需要临时回滚，可恢复本次 `pyproject.toml` 和 `uv.lock` 变更，但会重新暴露 AkShare 崩溃风险。
