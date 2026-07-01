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
http://127.0.0.1:8000/api/v1/health
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

## 部署

服务器部署脚本位于：

```bash
deploy/deploy.sh
```

首次部署前，在服务器项目根目录创建生产环境变量文件：

```bash
cp .env.production.example .env.production
vim .env.production
```

之后执行：

```bash
bash deploy/deploy.sh
```

默认部署 `master` 分支。脚本会执行：

- 拉取指定分支代码
- 构建并重启后端 Docker 容器
- 构建前端
- 将 `web/dist/` 里的内容同步到对应目录

指定部署分支：

```bash
bash deploy/deploy.sh dev
```

也可以使用环境变量指定：

```bash
SURFACE_GIT_BRANCH=dev bash deploy/deploy.sh
```

如果需要修改前端发布目录，在服务器的 `.env.production` 中配置：

```bash
SURFACE_WEB_TARGET=/var/www/surface/current
```

部署脚本会从 `.env.production` 读取 `SURFACE_WEB_TARGET`。

只部署前端：

```bash
bash deploy/deploy-web.sh
```

只部署前端并指定分支：

```bash
bash deploy/deploy-web.sh dev
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
