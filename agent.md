## Python Backend Development Rules

Python backend work in this project must follow `docs/v1.2.md`.

- Use `app/bootstrap.py`, `app/api/dependencies.py`, and `app/core/lifespan.py` as the composition and lifecycle boundary.
- Routers may orchestrate HTTP input/output only; they must not create database sessions, repositories, services, or infrastructure clients.
- Services receive a Unit of Work factory and decide use-case transaction boundaries.
- Repositories perform persistence operations but never call `commit()` or `rollback()`.
- Use explicit `uow.commit()` in successful write use cases. Uncommitted UoW exits roll back.
- Keep ORM models inside repositories and UoW-backed services. Map to DTOs or API-safe response models before returning.
- Do not raise FastAPI `HTTPException` from services. Raise application exceptions and let `app/core/exception.py` map them to HTTP responses.
- Do not keep a database session open while streaming SSE, calling LLMs, or waiting on external services. Use short UoW scopes before and after streaming.
- Health endpoints must preserve `/health/live`, `/health/ready`, and `/health/startup` semantics.
- If a future feature needs reliable asynchronous side effects, use Transactional Outbox rather than publishing critical events after commit.
