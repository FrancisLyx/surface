# Backend v1.2 Refactor Design

## Context

The backend is a FastAPI application with synchronous SQLAlchemy sessions, function-style service modules, and routers that pass `Session` objects directly into services. The project also has a new architecture standard in `docs/v1.2.md` that requires clear dependency composition, Unit of Work transaction boundaries, DTO isolation, domain exceptions, split health checks, and documented Python development rules in `agent.md`.

The refactor will apply the v1.2 rules across the Python backend while preserving the existing API contract for the frontend and tests. The only intentional API addition is the split health endpoints. The existing `/api/v1/health` endpoint remains as a compatibility alias for readiness.

## Goals

- Add a composition root and typed dependency providers.
- Move database transaction ownership out of routers and repositories.
- Migrate all Python service modules to injected service classes.
- Add a synchronous Unit of Work factory aligned with the current sync SQLAlchemy stack.
- Prevent ORM models from crossing route/service boundaries where practical.
- Replace service-layer `HTTPException` usage with domain/application exceptions.
- Split health checks into live, ready, and startup endpoints.
- Avoid long-lived database sessions during SSE streaming.
- Update `agent.md` so future Python backend work follows `docs/v1.2.md`.

## Non-Goals

- Do not convert the backend to async SQLAlchemy in this refactor.
- Do not change frontend route URLs or response envelopes.
- Do not introduce a message queue or full Transactional Outbox unless current code has a reliable-event use case that requires it.
- Do not reorganize the repository into a full `app/modules/*` bounded-context layout in this pass.

## Architecture

Add these backend architecture files:

- `app/bootstrap.py`: application-level dependency assembly helpers.
- `app/api/dependencies.py`: FastAPI dependency providers for services, settings, current user context, UoW factories, and request metadata.
- `app/core/lifespan.py`: startup state initialization and shutdown hooks.
- `app/core/exceptions.py` or an equivalent extension of `app/core/exception.py`: domain/application exception classes and HTTP mapping.
- `app/db/uow.py`: synchronous SQLAlchemy Unit of Work implementation.
- `app/repositories/*`: repository classes used by services through UoW.

`app/main.py` will become thin: create the app, register middleware, exception handlers, and routers, and delegate lifespan behavior to `app/core/lifespan.py`.

## Dependency Injection

Routers receive service instances through `Depends` and call service methods. Routers may still receive `Request` for the existing `success_response` envelope and request id, but they must not create database sessions, repositories, or infrastructure clients.

Services receive a `UnitOfWorkFactory` and any pure dependencies they need, such as fund data services or runtime services. Services must not import FastAPI request/response types or instantiate SQLAlchemy sessions.

Current authenticated user data should be exposed to routes and services as a lightweight context object, for example `CurrentUser(id, username, role_id)`, not as a live ORM object.

## Unit of Work

The project will use the v1.2 recommended use-case-level factory model with explicit commits:

- DI injects a UoW factory, not a live UoW.
- Each service use case opens `with self._uow_factory() as uow`.
- Repositories are only available while the UoW is active.
- Repositories never call `commit()`.
- Services decide when to call `uow.commit()`.
- `__exit__` rolls back when an exception occurs or when no explicit commit happened.
- `__exit__` always closes the session.

Because the backend currently uses sync FastAPI route handlers and sync SQLAlchemy, the UoW is synchronous. This keeps the refactor compatible with existing code and tests.

## Services

Migrate these modules to service classes:

- `user_service`
- `system_setting_service`
- `fund_favorite_service`
- `ai_fund_report_service`
- `agent_service`

Pure data-fetching services that call AkShare or LangChain can stay function-based if they do not manage infrastructure lifecycle, database sessions, or transaction boundaries. They should still be injected into higher-level services when used as collaborators.

Service methods return API-safe DTOs or current Pydantic response models. This is acceptable for this small project as long as the models do not depend on FastAPI HTTP concepts or live ORM state.

## Exceptions

Services must raise application/domain exceptions such as:

- `ValidationError` for bad business input.
- `UnauthorizedError` for authentication failures.
- `ForbiddenError` for denied business actions.
- `NotFoundError` for missing resources.
- `ConflictError` for duplicate records.

FastAPI-specific `HTTPException` should be limited to request/auth boundary code when unavoidable. The global exception handler maps application exceptions into the existing `ApiResponse` error envelope.

## ORM and DTO Boundary

ORM models remain inside repositories and UoW-backed services. Mapping to response DTOs must happen before the UoW closes. Route handlers must not return ORM models.

`get_current_user` should be refactored into a dependency that loads the user inside a short DB scope and returns a lightweight current-user context. Downstream services use `current_user.id` rather than accepting `User` ORM instances.

## Streaming

SSE endpoints must not keep a database session or transaction open while streaming LLM tokens or calling external tools.

For AI fund summaries:

1. Build and stream the summary without an open DB transaction.
2. Accumulate emitted text in the route/helper.
3. Persist the final report through `AiFundReportService` in a short UoW after streaming completes.

For agent chat:

1. Open a short UoW to ensure built-in agents, load agent metadata, create or load the conversation, and persist the user message/run start.
2. Stream model/tool events without holding the initial transaction open.
3. Persist tool messages, assistant message, and run status with short UoW operations.
4. On failure, persist failed run status in a short UoW and emit the current error event format.

This preserves behavior while following the v1.2 session lifetime rule.

## Health Checks

Expose:

- `GET /api/v1/health/live`: only reports the process is alive and never checks the database.
- `GET /api/v1/health/ready`: checks database connectivity and returns readiness.
- `GET /api/v1/health/startup`: reports whether lifespan initialization completed.
- `GET /api/v1/health`: compatibility alias for readiness.

Startup state is held in application state initialized by lifespan.

## `agent.md`

Update `agent.md` with a Python backend development section requiring:

- Follow `docs/v1.2.md`.
- Use DI providers and composition root.
- Inject UoW factories into services.
- Keep repositories commit-free.
- Keep ORM models inside the persistence/application boundary.
- Convert service errors to domain exceptions.
- Avoid long-lived DB sessions during streaming.
- Use split health checks for future health work.

## Testing

Tests should cover:

- UoW explicit commit and rollback-on-exit behavior.
- Application exception to API envelope mapping.
- Auth/current user context still works for `/user/me`.
- Existing user registration/login behavior.
- Existing favorite fund behavior and user scoping.
- AI report listing/detail behavior.
- Agent list/conversation/report behavior where current tests exist.
- Split health endpoints and compatibility `/health` alias.

Dependency overrides in tests should target the new providers while keeping compatibility where existing tests override `get_db`.
