# Strict Backend Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Python backend into strict alignment with `docs/架构与开发规范.md`.

**Architecture:** Keep the modular monolith, but complete the target-state infrastructure: Async SQLAlchemy, Alembic migrations, module-local DTOs, module-scoped UoW, API composition root, readiness monitoring, EventBus/Outbox/Inbox foundations, quality gates, and test layering. Move agent graph/tool code into the agent module so module boundaries match the business ownership.

**Tech Stack:** FastAPI, SQLAlchemy 2 Async, Alembic, Pydantic, Pytest, Ruff, Pyright, uv, Docker.

---

### Task 1: Architecture Guards

**Files:**
- Modify: `tests/test_app_module_structure.py`
- Test: `tests/test_app_module_structure.py`

- [ ] Add failing structure checks that require:
  - no `app/agents`
  - no `app/tools`
  - `app/modules/agent/graphs/fund_analysis.py`
  - `app/modules/agent/tools/fund.py`
  - `app/infrastructure/database/unit_of_work.py` uses async context methods
  - `alembic.ini`, `alembic/env.py`, and migration versions exist
  - `.pre-commit-config.yaml`, `compose.yml`, and `scripts/*.sh` exist

- [ ] Run:

```bash
uv run pytest tests/test_app_module_structure.py -q
```

Expected: FAIL because the strict target-state files are not all present yet.

### Task 2: Move Agent Graphs And Tools

**Files:**
- Move: `app/agents/fund_analysis_graph.py` -> `app/modules/agent/graphs/fund_analysis.py`
- Move: `app/tools/fund_tools.py` -> `app/modules/agent/tools/fund.py`
- Create: `app/modules/agent/graphs/__init__.py`
- Create: `app/modules/agent/tools/__init__.py`
- Modify: `app/modules/agent/runtime.py`
- Modify tests importing agent graph/tool modules

- [ ] Update imports so runtime loads graphs from `app.modules.agent.graphs.fund_analysis`.
- [ ] Update graph code to import agent tools from `app.modules.agent.tools.fund`.
- [ ] Remove old `app/agents` and `app/tools` packages.
- [ ] Run:

```bash
uv run pytest tests/test_tool_calling_agent.py tests/test_agent_routes.py -q
```

Expected: PASS.

### Task 3: Async SQLAlchemy Infrastructure

**Files:**
- Modify: `pyproject.toml`
- Modify: `app/infrastructure/database/session.py`
- Modify: `app/infrastructure/database/unit_of_work.py`
- Modify: module `uow.py` files
- Modify: repositories to use `AsyncSession`
- Modify: services to use `async with`
- Modify: routers to be `async def` where they call async services
- Modify: tests to use async-aware client patterns where needed

- [ ] Add async DB dependency support using `create_async_engine`, `async_sessionmaker`, and `AsyncSession`.
- [ ] Replace sync UoW context with `async __aenter__`, `async __aexit__`, `commit`, and `rollback`.
- [ ] Update repository methods to await SQLAlchemy calls.
- [ ] Update service methods that touch DB to async.
- [ ] Update route handlers that call async services to await.
- [ ] Keep external AkShare/LangChain calls synchronous unless the spec explicitly requires async clients; guard long calls outside DB transactions.
- [ ] Run:

```bash
uv run pytest tests/test_uow.py tests/test_user_routes.py tests/test_settings_routes.py tests/test_fund_favorite_routes.py tests/test_ai_routes.py tests/test_agent_routes.py -q
```

Expected: PASS.

### Task 4: Alembic Migration System

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/2026_07_02_0001_initial_schema.py`
- Modify: `app/infrastructure/database/session.py`
- Modify: `app/core/lifespan.py`
- Modify tests for migration presence

- [ ] Convert `app/sql/*.sql` schema into one initial Alembic migration.
- [ ] Keep `app/sql` only if explicitly treated as archived legacy reference, otherwise remove it.
- [ ] Remove startup `Base.metadata.create_all`.
- [ ] Lifespan must not auto-generate or auto-apply migrations.
- [ ] Run:

```bash
uv run alembic upgrade head
uv run pytest tests/test_app_module_structure.py -q
```

Expected: PASS.

### Task 5: DTO Boundary

**Files:**
- Create: module `dtos.py` files
- Modify: services to return DTOs
- Modify: routers to convert DTOs to API schemas
- Modify: tests to assert no service imports FastAPI and no ORM is returned

- [ ] Add dataclass DTOs for user, settings, fund favorites, AI reports, and agent list/report/conversation responses.
- [ ] Convert ORM to DTO while UoW session is open.
- [ ] Convert DTO to response schema in routers.
- [ ] Run:

```bash
uv run pytest tests/test_user_routes.py tests/test_settings_routes.py tests/test_fund_favorite_routes.py tests/test_ai_routes.py tests/test_agent_routes.py -q
```

Expected: PASS.

### Task 6: EventBus, Outbox, Inbox

**Files:**
- Create: `app/infrastructure/messaging/event_bus.py`
- Create: `app/infrastructure/outbox/models.py`
- Create: `app/infrastructure/outbox/repository.py`
- Create: `app/infrastructure/outbox/worker.py`
- Create: `app/infrastructure/inbox/models.py`
- Create: `app/infrastructure/inbox/repository.py`
- Modify: Alembic migration for outbox/inbox tables
- Modify: module UoW classes to expose outbox repository

- [ ] Implement serial in-process EventBus with failure isolation.
- [ ] Implement Outbox model/repository with status, retry count, next attempt, trace/request id fields.
- [ ] Implement Inbox model/repository with `(consumer_name, message_id)` unique constraint.
- [ ] Add Outbox repository to module UoW classes as the allowed cross-cutting exception.
- [ ] Run:

```bash
uv run pytest tests/unit tests/integration -q
```

Expected: PASS after tests are moved in Task 8.

### Task 7: Readiness Monitor And Graceful Lifespan

**Files:**
- Modify: `app/core/readiness.py`
- Modify: `app/core/lifespan.py`
- Modify: `app/modules/health/router.py`
- Add tests under `tests/api/test_health_routes.py` or existing health tests before move

- [ ] Add async background monitor task for core dependency checks.
- [ ] Checks must be lightweight and timeout-bound.
- [ ] `/health/ready` must read state; it may trigger a direct check in tests only through an injectable checker.
- [ ] Lifespan must cancel and await the monitor on shutdown.
- [ ] Run:

```bash
uv run pytest tests/test_health_routes.py -q
```

Expected: PASS.

### Task 8: Testing Layout And Quality Gates

**Files:**
- Move tests into `tests/unit`, `tests/integration`, `tests/api`, `tests/e2e`
- Modify: `pyproject.toml`
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/backend.yml`
- Create: `scripts/start.sh`
- Create: `scripts/test.sh`
- Create: `scripts/migrate.sh`
- Create or update: `compose.yml`

- [ ] Add Ruff, Pyright, Alembic, and pytest dev dependencies.
- [ ] Configure Ruff and Pyright in `pyproject.toml` or `pyrightconfig.json`.
- [ ] Move tests by layer and update imports.
- [ ] Add scripts matching the spec.
- [ ] Add CI workflow for Ruff, Pyright, pytest, Alembic migration smoke test, and Docker build.
- [ ] Run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q
```

Expected: PASS.

### Task 9: Final Verification

**Files:**
- Modify: `agent.md`
- Modify: docs if needed to record sync-to-async migration and current operational commands.

- [ ] Update `agent.md` to require strict spec layout, Async SQLAlchemy, Alembic, DTOs, readiness monitor, EventBus/Outbox/Inbox, and quality commands.
- [ ] Run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q
```

Expected: all commands pass.
