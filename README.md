# Surface

基于 FastAPI 的 Python 项目。

## 环境要求

- Python 3.12
- uv

如果本机尚未安装 `uv`，可参考官方安装方式：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 安装依赖

进入项目根目录后执行：

```bash
uv sync
```

该命令会根据 `pyproject.toml` 和 `uv.lock` 创建/更新虚拟环境，并安装项目依赖。

## 启动项目

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

## 常用命令

```bash
# 安装/同步依赖
uv sync

# 启动开发服务
uv run uvicorn app.main:app --reload

# 指定端口启动
uv run uvicorn app.main:app --reload --port 8001
```
