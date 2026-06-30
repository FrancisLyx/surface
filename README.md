# Surface

基于 FastAPI + React + Ant Design 的基金数据查询项目。

## 环境要求

- Python 3.12
- uv
- Node.js
- npm

如果本机尚未安装 `uv`，可参考官方安装方式：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 后端依赖安装

进入项目根目录后执行：

```bash
uv sync
```

该命令会根据 `pyproject.toml` 和 `uv.lock` 创建/更新虚拟环境，并安装项目依赖。

## 前端依赖安装

进入前端目录后执行：

```bash
cd web
npm install
```

## 启动后端

开发环境启动：

```bash
uv run uvicorn app.main:app --reload
```

默认访问地址：

```text
http://127.0.0.1:8000
```

健康检查接口：

```text
http://127.0.0.1:8000/health
```

## 启动前端

另开一个终端，进入前端目录后执行：

```bash
cd web
npm run dev
```

默认访问地址：

```text
http://127.0.0.1:5173
```

前端开发服务已配置代理：

```text
/api -> http://127.0.0.1:8000
```

因此本地开发时需要先启动后端，再启动前端。

如果需要指定后端地址，也可以在 `web/.env` 中配置：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## 构建前端

```bash
cd web
npm run build
```

构建产物位于：

```text
web/dist
```

## 运行测试

后端测试：

```bash
uv run python -m pytest
```

前端构建校验：

```bash
cd web
npm run build
```

## 常用命令

```bash
# 安装/同步后端依赖
uv sync

# 启动后端开发服务
uv run uvicorn app.main:app --reload

# 指定后端端口启动
uv run uvicorn app.main:app --reload --port 8001

# 安装前端依赖
cd web && npm install

# 启动前端开发服务
cd web && npm run dev

# 构建前端
cd web && npm run build
```
