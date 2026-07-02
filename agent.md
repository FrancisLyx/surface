## Python Backend Development Rules

Python backend work in this project must follow `docs/架构与开发规范.md`.

- Use `app/bootstrap.py`, `app/api/dependencies.py`, and `app/core/lifespan.py` as the composition and lifecycle boundary.
- Use `app/api/router.py` to compose HTTP routers and `app/api/error_handlers.py` to register API error handling.
- Keep database infrastructure under `app/infrastructure/database/` and external clients under `app/infrastructure/clients/`.
- Use SQLAlchemy Async APIs only in application code: `AsyncSession`, `async_sessionmaker`, `create_async_engine`, and `async with` UoW scopes. Do not reintroduce `sqlalchemy.orm.Session` in `app/`.
- Database schema changes must be represented by Alembic migrations in `alembic/versions/`. Do not call `Base.metadata.create_all()` from application startup; tests may create isolated schemas in test helpers only.
- Module HTTP entry files are named `router.py`; Pydantic API contracts are `schemas.py`; ORM files are `models.py`; domain event helpers are `events.py`.
- Application DTOs live in each module's `dtos.py`. Services must not return live ORM objects across the application boundary.
- Routers may orchestrate HTTP input/output only; they must not create database sessions, repositories, services, or infrastructure clients.
- Services receive a module-scoped Unit of Work factory and decide use-case transaction boundaries.
- Repositories perform persistence operations but never call `commit()` or `rollback()`.
- Use explicit `uow.commit()` in successful write use cases. Uncommitted UoW exits roll back.
- `app/infrastructure/database/unit_of_work.py` is transaction infrastructure only. Do not add business repositories to it.
- Each business module owns its own `uow.py`; module UoW classes may expose only repositories from that module.
- `OutboxRepository` is the only cross-cutting repository allowed in module UoW classes, because it participates in the same transaction as the module write.
- Do not create a cross-module or global "god UoW". If two modules need atomic writes, revisit the module boundary or use Outbox-based eventual consistency.
- Cross-module reads or synchronous collaboration must go through the target module's `public.py` facade/query service, not its ORM models, repositories, or internal service implementation.
- Keep ORM models inside repositories and UoW-backed services. Map to DTOs or API-safe response models before returning.
- Do not raise FastAPI `HTTPException` from services. Raise `DomainError`/application exceptions and let `app/core/exception.py` map them to HTTP responses.
- Do not keep a database session open while streaming SSE, calling LLMs, or waiting on external services. Use short UoW scopes before and after streaming.
- Health endpoints must preserve `/health/live`, `/health/ready`, and `/health/startup` semantics. `live` must not touch external dependencies; `ready` must reflect observable core dependency state and the lifespan readiness monitor must be cancellable during shutdown.
- Use `app/infrastructure/messaging/event_bus.py` only for non-critical in-process side effects. Handlers are serial and failure-isolated by default.
- Critical asynchronous side effects must use Transactional Outbox (`app/infrastructure/outbox/`) and consumers must use Inbox/idempotency records (`app/infrastructure/inbox/`) rather than publishing critical events after commit.
- Keep agent graphs/tools inside `app/modules/agent/graphs/` and `app/modules/agent/tools/`; do not recreate top-level `app/agents` or `app/tools`.
- Keep tests organized by intent under `tests/unit`, `tests/integration`, `tests/api`, and `tests/e2e` when adding new coverage.
- Before completing Python backend work, run `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest -q`.
