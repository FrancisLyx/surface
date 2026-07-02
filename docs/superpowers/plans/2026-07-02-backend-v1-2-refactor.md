# Backend v1.2 Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the FastAPI backend to follow `docs/v1.2.md` across dependency injection, Unit of Work transactions, ORM boundaries, exceptions, health checks, streaming session lifetime, and project rules.

**Architecture:** Keep the existing sync FastAPI and sync SQLAlchemy stack, but add a composition root, repository layer, synchronous UoW factory, service classes, and lightweight current-user context. Preserve existing route URLs and response envelopes, with `/api/v1/health` kept as a compatibility alias for readiness.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 sync ORM, Pydantic, pytest, FastAPI TestClient.

---

## File Structure

- Create `app/api/dependencies.py`: all FastAPI providers for settings, UoW factory, service classes, and current user context.
- Create `app/bootstrap.py`: pure factory helpers for UoW and service construction.
- Create `app/core/lifespan.py`: app startup/readiness state and database initialization.
- Modify `app/core/exception.py`: add application exception classes and map them to the existing API error envelope.
- Create `app/core/current_user.py`: immutable current-user context DTO.
- Modify `app/core/security.py`: keep password/JWT helpers; move authenticated-user dependency behavior to `app/api/dependencies.py`.
- Modify `app/db/session.py`: keep global engine/session factory and compatibility `get_db`; add helper for creating session factories if tests need it.
- Create `app/db/uow.py`: sync SQLAlchemy UoW with explicit commit and rollback-on-exit.
- Create `app/repositories/__init__.py`: repository package marker.
- Create `app/repositories/users.py`: user queries and writes.
- Create `app/repositories/system_settings.py`: system setting queries and writes.
- Create `app/repositories/fund_favorites.py`: favorite fund queries and writes.
- Create `app/repositories/ai_fund_reports.py`: AI report queries and writes.
- Create `app/repositories/agents.py`: agent definition, conversation, message, run, and report queries/writes.
- Modify `app/services/user_service.py`: service class using UoW factory and domain exceptions.
- Modify `app/services/system_setting_service.py`: service class using UoW factory.
- Modify `app/services/fund_favorite_service.py`: service class using UoW factory and current-user context.
- Modify `app/services/ai_fund_report_service.py`: service class using UoW factory and current-user context.
- Modify `app/services/agent_service.py`: service class using UoW factory, short DB scopes, and no `HTTPException`.
- Modify route files under `app/api/routes/*/*_view.py`: inject services/current user through `app/api/dependencies.py`.
- Modify `app/api/routes/health/health_view.py`: split live/ready/startup and keep compatibility alias.
- Modify `app/main.py`: use `app_lifespan` and keep router registration thin.
- Modify `agent.md`: add Python backend rules requiring `docs/v1.2.md`.
- Add/modify tests under `tests/`: UoW, exception mapping, health split, and route compatibility.

---

### Task 1: Foundation Exceptions, Current User, UoW, and Health

**Files:**
- Create: `app/core/current_user.py`
- Create: `app/db/uow.py`
- Create: `tests/test_uow.py`
- Create: `tests/test_exception_mapping.py`
- Modify: `app/core/exception.py`
- Modify: `app/api/routes/health/health_view.py`
- Modify: `tests/test_health_routes.py`

- [ ] **Step 1: Write failing UoW tests**

Create `tests/test_uow.py`:

```python
import pytest

from app.db.uow import SqlAlchemyUnitOfWork


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closes += 1


def test_uow_rolls_back_and_closes_when_not_committed():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with uow:
        assert uow.session is session

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


def test_uow_commits_explicitly_and_closes_without_rollback():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with uow:
        uow.commit()

    assert session.commits == 1
    assert session.rollbacks == 0
    assert session.closes == 1


def test_uow_rolls_back_exception_even_after_no_commit():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with pytest.raises(RuntimeError, match="boom"):
        with uow:
            raise RuntimeError("boom")

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


def test_uow_rejects_session_access_outside_context():
    uow = SqlAlchemyUnitOfWork(lambda: FakeSession())

    with pytest.raises(RuntimeError, match="Unit of Work is not active"):
        _ = uow.session
```

- [ ] **Step 2: Run UoW test to verify it fails**

Run: `uv run pytest tests/test_uow.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'app.db.uow'`.

- [ ] **Step 3: Implement current-user DTO and UoW**

Create `app/core/current_user.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: int
    username: str
    email: str | None = None
    phone: str | None = None
    role_id: int | None = None
```

Create `app/db/uow.py`:

```python
from collections.abc import Callable
from types import TracebackType
from typing import Any, Self

from sqlalchemy.orm import Session


SessionFactory = Callable[[], Session]


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is not None or not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of Work is not active")
        return self._session

    def commit(self) -> None:
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(name)
```

- [ ] **Step 4: Run UoW test to verify it passes**

Run: `uv run pytest tests/test_uow.py -v`

Expected: PASS.

- [ ] **Step 5: Write failing application-exception mapping test**

Create `tests/test_exception_mapping.py`:

```python
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.exception import NotFoundError, register_exception_handlers
from app.core.response import success_response


def test_application_exception_maps_to_api_error_envelope():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/missing")
    def missing():
        raise NotFoundError("thing not found")

    response = TestClient(app).get("/missing")

    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["message"] == "thing not found"


def test_success_response_still_works_with_registered_handlers():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/ok")
    def ok(request: Request):
        return success_response(request, {"ok": True})

    response = TestClient(app).get("/ok")

    assert response.status_code == 200
    assert response.json()["data"] == {"ok": True}
```

- [ ] **Step 6: Run exception test to verify it fails**

Run: `uv run pytest tests/test_exception_mapping.py -v`

Expected: FAIL with `ImportError` for `NotFoundError`.

- [ ] **Step 7: Implement application exceptions and mapping**

Modify `app/core/exception.py`:

```python
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import error_response

logger = logging.getLogger("app.exception")


class ApplicationError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(ApplicationError):
    status_code = 400


class UnauthorizedError(ApplicationError):
    status_code = 401


class ForbiddenError(ApplicationError):
    status_code = 403


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 400


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def application_exception_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        return _error_response(request, exc.status_code, exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(request, exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _error_response(request, 422, "Request validation failed")

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception request_id=%s", _get_request_id(request), exc_info=exc)
        return _error_response(request, 500, "Internal server error")


def _error_response(request: Request, status_code: int, message: str) -> JSONResponse:
    payload = error_response(request, status_code, message)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")
```

- [ ] **Step 8: Run exception test to verify it passes**

Run: `uv run pytest tests/test_exception_mapping.py -v`

Expected: PASS.

- [ ] **Step 9: Write failing split health tests**

Modify `tests/test_health_routes.py`:

```python
from fastapi.testclient import TestClient

from app.db import session as db_session
from app.main import app


def test_liveness_does_not_open_database_session():
    def fail_get_db():
        raise AssertionError("live health must not access database")
        yield

    app.dependency_overrides[db_session.get_db] = fail_get_db
    try:
        response = TestClient(app).get("/api/v1/health/live")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "service": "alive",
    }


def test_readiness_reports_database_ok():
    class FakeScalarResult:
        def scalar_one(self):
            return 1

    class FakeSession:
        def execute(self, statement):
            return FakeScalarResult()

        def close(self):
            pass

    def fake_get_db():
        yield FakeSession()

    app.dependency_overrides[db_session.get_db] = fake_get_db
    try:
        response = TestClient(app).get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["data"] == {
        "status": "ok",
        "database": "ok",
    }


def test_health_alias_reports_readiness():
    class FakeScalarResult:
        def scalar_one(self):
            return 1

    class FakeSession:
        def execute(self, statement):
            return FakeScalarResult()

        def close(self):
            pass

    def fake_get_db():
        yield FakeSession()

    app.dependency_overrides[db_session.get_db] = fake_get_db
    try:
        response = TestClient(app).get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "database": "ok",
    }


def test_startup_reports_initialized_state():
    response = TestClient(app).get("/api/v1/health/startup")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
    assert response.json()["data"]["startup_complete"] is True
```

- [ ] **Step 10: Run health tests to verify they fail**

Run: `uv run pytest tests/test_health_routes.py -v`

Expected: FAIL with 404 for `/health/live`, `/health/ready`, or `/health/startup`.

- [ ] **Step 11: Implement split health endpoints**

Modify `app/api/routes/health/health_view.py`:

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, success_response
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=ApiResponse, summary="存活检查")
def liveness_check(request: Request) -> ApiResponse:
    return success_response(request, {"status": "ok", "service": "alive"})


@router.get("/ready", response_model=ApiResponse, summary="就绪检查")
def readiness_check(request: Request, db: Session = Depends(get_db)) -> ApiResponse:
    db.execute(text("select 1")).scalar_one()
    return success_response(request, {"status": "ok", "database": "ok"})


@router.get("/startup", response_model=ApiResponse, summary="启动检查")
def startup_check(request: Request) -> ApiResponse:
    startup_complete = bool(getattr(request.app.state, "startup_complete", True))
    return success_response(
        request,
        {
            "status": "ok" if startup_complete else "starting",
            "startup_complete": startup_complete,
        },
    )


@router.get("", response_model=ApiResponse, summary="健康检查")
def health_check(request: Request, db: Session = Depends(get_db)) -> ApiResponse:
    return readiness_check(request, db)
```

- [ ] **Step 12: Run foundation tests**

Run: `uv run pytest tests/test_uow.py tests/test_exception_mapping.py tests/test_health_routes.py -v`

Expected: PASS.

- [ ] **Step 13: Commit foundation**

```bash
git add app/core/current_user.py app/db/uow.py app/core/exception.py app/api/routes/health/health_view.py tests/test_uow.py tests/test_exception_mapping.py tests/test_health_routes.py
git commit -m "feat: add backend v1.2 foundation"
```

---

### Task 2: Composition Root, Repositories, User, Settings, and Auth Context

**Files:**
- Create: `app/repositories/__init__.py`
- Create: `app/repositories/users.py`
- Create: `app/repositories/system_settings.py`
- Create: `app/bootstrap.py`
- Create: `app/api/dependencies.py`
- Modify: `app/services/user_service.py`
- Modify: `app/services/system_setting_service.py`
- Modify: `app/api/routes/user/user_view.py`
- Modify: `app/api/routes/settings/settings_view.py`
- Modify: `app/core/security.py`
- Modify: `tests/test_user_routes.py`
- Modify: `tests/test_settings_routes.py`

- [ ] **Step 1: Write failing user/settings architecture tests**

Add to `tests/test_user_routes.py`:

```python
def test_user_service_uses_domain_exception_for_duplicate_username(monkeypatch):
    from app.core.exception import ConflictError
    from app.services.user_service import UserService

    class FakeUsers:
        def get_by_username(self, username):
            return object()

    class FakeSettings:
        def is_registration_enabled(self):
            return True

    class FakeUow:
        users = FakeUsers()
        system_settings = FakeSettings()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    service = UserService(lambda: FakeUow())

    with pytest.raises(ConflictError, match="username already exists"):
        service.register_user(
            UserRegisterRequest(
                username="admin",
                email="admin@example.com",
                phone="13800138000",
                password="123456",
            )
        )
```

At the top of `tests/test_user_routes.py`, add:

```python
import pytest
```

Add to `tests/test_settings_routes.py`:

```python
def test_settings_route_still_controls_register_flow_through_service(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = make_client()
    try:
        token = register_and_login(client)

        response = client.post(
            "/api/v1/settings/registration",
            json={"enabled": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["data"] == {"enabled": False}
    finally:
        clear_overrides()
```

- [ ] **Step 2: Run user/settings tests to verify they fail**

Run: `uv run pytest tests/test_user_routes.py::test_user_service_uses_domain_exception_for_duplicate_username tests/test_settings_routes.py::test_settings_route_still_controls_register_flow_through_service -v`

Expected: FAIL because `UserService` is not defined.

- [ ] **Step 3: Implement user and settings repositories**

Create `app/repositories/__init__.py`:

```python
"""Persistence repositories."""
```

Create `app/repositories/users.py`:

```python
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        return self._session.scalar(select(User).where(User.id == user_id))

    def get_active_by_id(self, user_id: int) -> User | None:
        return self._session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))

    def get_by_username(self, username: str) -> User | None:
        return self._session.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))

    def get_by_phone(self, phone: str) -> User | None:
        return self._session.scalar(select(User).where(User.phone == phone))

    def get_by_account(self, account: str) -> User | None:
        return self._session.scalar(
            select(User).where(
                or_(
                    User.username == account,
                    User.email == account.lower(),
                    User.phone == account,
                )
            )
        )

    def add(self, user: User) -> None:
        self._session.add(user)

    def refresh(self, user: User) -> None:
        self._session.refresh(user)
```

Create `app/repositories/system_settings.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import is_user_registration_enabled as get_env_registration_enabled
from app.db.models.system_setting import SystemSetting

USER_REGISTRATION_ENABLED_KEY = "user_registration_enabled"


class SystemSettingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def is_registration_enabled(self) -> bool:
        setting = self._session.scalar(
            select(SystemSetting).where(SystemSetting.key == USER_REGISTRATION_ENABLED_KEY)
        )
        if setting is None:
            return get_env_registration_enabled()
        return _setting_value_to_bool(setting.value)

    def set_registration_enabled(self, enabled: bool) -> None:
        setting = self._session.get(SystemSetting, USER_REGISTRATION_ENABLED_KEY)
        if setting is None:
            setting = SystemSetting(key=USER_REGISTRATION_ENABLED_KEY, value=_bool_to_setting_value(enabled))
            self._session.add(setting)
        else:
            setting.value = _bool_to_setting_value(enabled)


def _bool_to_setting_value(value: bool) -> str:
    return "true" if value else "false"


def _setting_value_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
```

- [ ] **Step 4: Extend UoW with repositories**

Modify `app/db/uow.py`:

```python
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session

from app.repositories.system_settings import SystemSettingRepository
from app.repositories.users import UserRepository


SessionFactory = Callable[[], Session]


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self._committed = False
        self.users = UserRepository(self._session)
        self.system_settings = SystemSettingRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return

        try:
            if exc_type is not None or not self._committed:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Unit of Work is not active")
        return self._session

    def commit(self) -> None:
        self.session.commit()
        self._committed = True

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
```

- [ ] **Step 5: Implement user/settings service classes**

Modify `app/services/user_service.py`:

```python
from collections.abc import Callable

from app.api.routes.user.user_schema import LoginResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.core.current_user import CurrentUser
from app.core.exception import ConflictError, ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import User


class UserService:
    def __init__(self, uow_factory: Callable) -> None:
        self._uow_factory = uow_factory

    def get_register_status(self) -> dict[str, bool]:
        with self._uow_factory() as uow:
            return {"enabled": uow.system_settings.is_registration_enabled()}

    def register_user(self, payload: UserRegisterRequest) -> UserResponse:
        with self._uow_factory() as uow:
            if not uow.system_settings.is_registration_enabled():
                raise ForbiddenError("registration is disabled")

            username = payload.username.strip()
            email = str(payload.email).strip().lower() if payload.email else None
            phone = payload.phone.strip() if payload.phone else None

            if uow.users.get_by_username(username) is not None:
                raise ConflictError("username already exists")
            if email and uow.users.get_by_email(email) is not None:
                raise ConflictError("email already exists")
            if phone and uow.users.get_by_phone(phone) is not None:
                raise ConflictError("phone already exists")

            user = User(
                username=username,
                email=email,
                phone=phone,
                password_hash=hash_password(payload.password),
            )
            uow.users.add(user)
            uow.commit()
            uow.users.refresh(user)
            return build_user_response(user)

    def login_user(self, payload: UserLoginRequest) -> LoginResponse:
        account = payload.account.strip()
        with self._uow_factory() as uow:
            user = uow.users.get_by_account(account)
            if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
                raise UnauthorizedError("invalid account or password")

            return LoginResponse(
                access_token=create_access_token(user),
                user=build_user_response(user),
            )


def build_user_response(user: User | CurrentUser) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
    )
```

Modify `app/services/system_setting_service.py`:

```python
from collections.abc import Callable


class SystemSettingService:
    def __init__(self, uow_factory: Callable) -> None:
        self._uow_factory = uow_factory

    def get_registration_setting(self) -> dict[str, bool]:
        with self._uow_factory() as uow:
            return {"enabled": uow.system_settings.is_registration_enabled()}

    def update_registration_setting(self, enabled: bool) -> dict[str, bool]:
        with self._uow_factory() as uow:
            uow.system_settings.set_registration_enabled(enabled)
            uow.commit()
            return {"enabled": enabled}
```

- [ ] **Step 6: Implement bootstrap and dependencies**

Create `app/bootstrap.py`:

```python
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db.uow import SqlAlchemyUnitOfWork
from app.services.system_setting_service import SystemSettingService
from app.services.user_service import UserService


def create_uow_factory(session_factory: Callable[[], Session]) -> Callable[[], SqlAlchemyUnitOfWork]:
    return lambda: SqlAlchemyUnitOfWork(session_factory)


def create_user_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> UserService:
    return UserService(uow_factory)


def create_system_setting_service(uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> SystemSettingService:
    return SystemSettingService(uow_factory)
```

Create `app/api/dependencies.py`:

```python
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.bootstrap import create_system_setting_service, create_uow_factory, create_user_service
from app.core.config import Settings, get_settings
from app.core.current_user import CurrentUser
from app.core.security import bearer_scheme
from app.db.session import SessionLocal, get_db
from app.db.uow import SqlAlchemyUnitOfWork
from app.services.system_setting_service import SystemSettingService
from app.services.user_service import UserService


SettingsDep = Annotated[Settings, Depends(get_settings)]
UowFactory = Callable[[], SqlAlchemyUnitOfWork]


def get_uow_factory() -> UowFactory:
    return create_uow_factory(SessionLocal)


def get_user_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> UserService:
    return create_user_service(uow_factory)


def get_system_setting_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> SystemSettingService:
    return create_system_setting_service(uow_factory)


def get_current_user_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: SettingsDep,
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = int(payload.get("sub", ""))
    except (JWTError, ValueError):
        raise _unauthorized() from None

    with uow_factory() as uow:
        user = uow.users.get_active_by_id(user_id)
        if user is None:
            raise _unauthorized()
        return CurrentUser(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            role_id=user.role_id,
        )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
```

- [ ] **Step 7: Keep security compatibility wrapper**

Modify `app/core/security.py` so it only owns crypto helpers plus a compatibility import:

```python
from datetime import datetime, timedelta, timezone

from fastapi.security import HTTPBearer
from passlib.context import CryptContext
from jose import jwt

from app.core.config import get_settings
from app.db.models.user import User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user: User) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(*args, **kwargs):
    from app.api.dependencies import get_current_user_context

    return get_current_user_context(*args, **kwargs)
```

- [ ] **Step 8: Refactor user and settings routes**

Modify `app/api/routes/user/user_view.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_current_user_context, get_user_service
from app.api.routes.user.user_schema import UserLoginRequest, UserRegisterRequest
from app.core.current_user import CurrentUser
from app.core.response import ApiResponse, success_response
from app.services.user_service import UserService, build_user_response

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/register-status", response_model=ApiResponse, summary="查询注册开关")
def get_register_status(
    request: Request,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.get_register_status())


@router.post("/register", response_model=ApiResponse, summary="用户注册")
def register_user(
    request: Request,
    payload: UserRegisterRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.register_user(payload))


@router.post("/login", response_model=ApiResponse, summary="用户登录")
def login_user(
    request: Request,
    payload: UserLoginRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> ApiResponse:
    return success_response(request, service.login_user(payload))


@router.get("/me", response_model=ApiResponse, summary="当前用户")
def get_me(
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, build_user_response(current_user))
```

Modify `app/api/routes/settings/settings_view.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_system_setting_service
from app.api.routes.settings.settings_schema import RegistrationSettingRequest
from app.core.auth import require_auth
from app.core.response import ApiResponse, success_response
from app.services.system_setting_service import SystemSettingService

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[require_auth()])


@router.get("/registration", response_model=ApiResponse, summary="查询注册设置")
def get_registration_setting(
    request: Request,
    service: Annotated[SystemSettingService, Depends(get_system_setting_service)],
) -> ApiResponse:
    return success_response(request, service.get_registration_setting())


@router.post("/registration", response_model=ApiResponse, summary="更新注册设置")
def update_registration_setting(
    request: Request,
    payload: RegistrationSettingRequest,
    service: Annotated[SystemSettingService, Depends(get_system_setting_service)],
) -> ApiResponse:
    return success_response(request, service.update_registration_setting(payload.enabled))
```

- [ ] **Step 9: Run user/settings route tests**

Run: `uv run pytest tests/test_user_routes.py tests/test_settings_routes.py -v`

Expected: PASS.

- [ ] **Step 10: Commit user/settings migration**

```bash
git add app/repositories app/bootstrap.py app/api/dependencies.py app/db/uow.py app/core/security.py app/services/user_service.py app/services/system_setting_service.py app/api/routes/user/user_view.py app/api/routes/settings/settings_view.py tests/test_user_routes.py tests/test_settings_routes.py
git commit -m "refactor: migrate user and settings services to uow"
```

---

### Task 3: Favorite Funds and AI Reports Service Migration

**Files:**
- Create: `app/repositories/fund_favorites.py`
- Create: `app/repositories/ai_fund_reports.py`
- Modify: `app/db/uow.py`
- Modify: `app/bootstrap.py`
- Modify: `app/api/dependencies.py`
- Modify: `app/services/fund_favorite_service.py`
- Modify: `app/services/ai_fund_report_service.py`
- Modify: `app/api/routes/fund/fund_view.py`
- Modify: `app/api/routes/ai/ai_view.py`
- Modify: `tests/test_fund_favorite_routes.py`
- Modify: `tests/test_ai_routes.py`

- [ ] **Step 1: Write failing service-boundary tests**

Add to `tests/test_fund_favorite_routes.py`:

```python
def test_favorite_service_accepts_current_user_context(monkeypatch):
    from app.core.current_user import CurrentUser
    from app.services.fund_favorite_service import FundFavoriteService

    class FakeFavorites:
        def __init__(self):
            self.added_user_id = None

        def get_by_user_and_code(self, user_id, fund_code):
            return None

        def add(self, favorite):
            self.added_user_id = favorite.user_id

        def refresh(self, favorite):
            favorite.id = 10
            favorite.created_at = favorite.created_at or __import__("datetime").datetime(2026, 1, 1)

    class FakeUow:
        def __init__(self):
            self.fund_favorites = FakeFavorites()
            self.committed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def commit(self):
            self.committed = True

    uow = FakeUow()
    service = FundFavoriteService(lambda: uow)
    result = service.add_favorite_fund(
        CurrentUser(id=7, username="admin"),
        FavoriteFundAddRequest(fund_code="000001", fund_name="华夏成长混合", fund_type="混合型"),
    )

    assert uow.fund_favorites.added_user_id == 7
    assert uow.committed is True
    assert result.fund_code == "000001"
```

Add to `tests/test_ai_routes.py`:

```python
def test_ai_report_service_returns_not_found_for_other_user():
    import pytest
    from app.core.current_user import CurrentUser
    from app.core.exception import NotFoundError
    from app.services.ai_fund_report_service import AiFundReportService

    class FakeReports:
        def get_by_id_for_user(self, report_id, user_id):
            return None

    class FakeUow:
        ai_fund_reports = FakeReports()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    service = AiFundReportService(lambda: FakeUow())

    with pytest.raises(NotFoundError, match="report not found"):
        service.get_report_detail(CurrentUser(id=2, username="guest"), 1)
```

- [ ] **Step 2: Run new boundary tests to verify they fail**

Run: `uv run pytest tests/test_fund_favorite_routes.py::test_favorite_service_accepts_current_user_context tests/test_ai_routes.py::test_ai_report_service_returns_not_found_for_other_user -v`

Expected: FAIL because `FundFavoriteService` or `AiFundReportService` are not implemented.

- [ ] **Step 3: Implement fund favorite repository**

Create `app/repositories/fund_favorites.py`:

```python
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.fund_favorite import UserFavoriteFund


class FundFavoriteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_and_code(self, user_id: int, fund_code: str) -> UserFavoriteFund | None:
        return self._session.scalar(
            select(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )

    def count_for_user(self, user_id: int, keyword: str | None = None) -> int:
        where_clause = self._where_clause(user_id, keyword)
        return self._session.scalar(select(func.count()).select_from(UserFavoriteFund).where(where_clause)) or 0

    def list_for_user(
        self,
        user_id: int,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UserFavoriteFund]:
        return list(
            self._session.scalars(
                select(UserFavoriteFund)
                .where(self._where_clause(user_id, keyword))
                .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def list_options_for_user(self, user_id: int) -> list[UserFavoriteFund]:
        return list(
            self._session.scalars(
                select(UserFavoriteFund)
                .where(UserFavoriteFund.user_id == user_id)
                .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
            ).all()
        )

    def add(self, favorite: UserFavoriteFund) -> None:
        self._session.add(favorite)

    def refresh(self, favorite: UserFavoriteFund) -> None:
        self._session.refresh(favorite)

    def remove_for_user(self, user_id: int, fund_code: str) -> int:
        result = self._session.execute(
            delete(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )
        return result.rowcount or 0

    def _where_clause(self, user_id: int, keyword: str | None):
        filters = [UserFavoriteFund.user_id == user_id]
        normalized_keyword = keyword.strip() if keyword else None
        if normalized_keyword:
            like_keyword = f"%{normalized_keyword}%"
            filters.append(
                or_(
                    UserFavoriteFund.fund_code.ilike(like_keyword),
                    UserFavoriteFund.fund_name.ilike(like_keyword),
                    UserFavoriteFund.fund_type.ilike(like_keyword),
                )
            )
        return and_(*filters)
```

- [ ] **Step 4: Implement AI fund report repository**

Create `app/repositories/ai_fund_reports.py`:

```python
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.models.ai_fund_report import AiFundReport


class AiFundReportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, report: AiFundReport) -> None:
        self._session.add(report)

    def refresh(self, report: AiFundReport) -> None:
        self._session.refresh(report)

    def count_for_user(self, user_id: int, fund_code: str | None = None) -> int:
        return self._session.scalar(
            select(func.count()).select_from(AiFundReport).where(self._where_clause(user_id, fund_code))
        ) or 0

    def list_for_user(
        self,
        user_id: int,
        fund_code: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[AiFundReport]:
        return list(
            self._session.scalars(
                select(AiFundReport)
                .where(self._where_clause(user_id, fund_code))
                .order_by(AiFundReport.created_at.desc(), AiFundReport.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def get_by_id_for_user(self, report_id: int, user_id: int) -> AiFundReport | None:
        return self._session.scalar(
            select(AiFundReport).where(
                AiFundReport.id == report_id,
                AiFundReport.user_id == user_id,
            )
        )

    def _where_clause(self, user_id: int, fund_code: str | None):
        filters = [AiFundReport.user_id == user_id]
        normalized_fund_code = fund_code.strip() if fund_code else None
        if normalized_fund_code:
            filters.append(AiFundReport.fund_code == normalized_fund_code)
        return and_(*filters)
```

- [ ] **Step 5: Extend UoW and bootstrap/dependencies**

Modify `app/db/uow.py` imports and `__enter__`:

```python
from app.repositories.ai_fund_reports import AiFundReportRepository
from app.repositories.fund_favorites import FundFavoriteRepository
```

Inside `__enter__`, after existing repository assignments:

```python
self.fund_favorites = FundFavoriteRepository(self._session)
self.ai_fund_reports = AiFundReportRepository(self._session)
```

Modify `app/bootstrap.py`:

```python
from app.services.ai_fund_report_service import AiFundReportService
from app.services.fund_favorite_service import FundFavoriteService
```

Add:

```python
def create_fund_favorite_service(uow_factory):
    return FundFavoriteService(uow_factory)


def create_ai_fund_report_service(uow_factory):
    return AiFundReportService(uow_factory)
```

Modify `app/api/dependencies.py` imports and providers:

```python
from app.bootstrap import (
    create_ai_fund_report_service,
    create_fund_favorite_service,
    create_system_setting_service,
    create_uow_factory,
    create_user_service,
)
from app.services.ai_fund_report_service import AiFundReportService
from app.services.fund_favorite_service import FundFavoriteService
```

Add:

```python
def get_fund_favorite_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> FundFavoriteService:
    return create_fund_favorite_service(uow_factory)


def get_ai_fund_report_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> AiFundReportService:
    return create_ai_fund_report_service(uow_factory)
```

- [ ] **Step 6: Implement favorite and report service classes**

Modify `app/services/ai_fund_report_service.py`:

```python
from collections.abc import Callable

from app.api.routes.ai.ai_schema import AiFundReportDetailResponse, AiFundReportListItem
from app.core.current_user import CurrentUser
from app.core.exception import NotFoundError
from app.core.pagination import PageResponse
from app.db.models.ai_fund_report import AiFundReport


class AiFundReportService:
    def __init__(self, uow_factory: Callable) -> None:
        self._uow_factory = uow_factory

    def create_report(self, user: CurrentUser, fund_code: str, content: str) -> AiFundReportDetailResponse:
        with self._uow_factory() as uow:
            report = AiFundReport(
                user_id=user.id,
                fund_code=fund_code.strip(),
                content=content,
            )
            uow.ai_fund_reports.add(report)
            uow.commit()
            uow.ai_fund_reports.refresh(report)
            return _to_detail_item(report)

    def list_reports(
        self,
        user: CurrentUser,
        fund_code: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PageResponse[AiFundReportListItem]:
        with self._uow_factory() as uow:
            total = uow.ai_fund_reports.count_for_user(user.id, fund_code)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            reports = uow.ai_fund_reports.list_for_user(user.id, fund_code, offset=offset, limit=page_size)
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_list_item(report) for report in reports],
            )

    def get_report_detail(self, user: CurrentUser, report_id: int) -> AiFundReportDetailResponse:
        with self._uow_factory() as uow:
            report = uow.ai_fund_reports.get_by_id_for_user(report_id, user.id)
            if report is None:
                raise NotFoundError("report not found")
            return _to_detail_item(report)


def _to_list_item(report: AiFundReport) -> AiFundReportListItem:
    return AiFundReportListItem(
        id=report.id,
        fund_code=report.fund_code,
        created_at=report.created_at.isoformat(),
    )


def _to_detail_item(report: AiFundReport) -> AiFundReportDetailResponse:
    return AiFundReportDetailResponse(
        id=report.id,
        fund_code=report.fund_code,
        content=report.content,
        created_at=report.created_at.isoformat(),
    )
```

Modify `app/services/fund_favorite_service.py` by wrapping existing helpers in a `FundFavoriteService` class. Keep `_load_favorite_estimations`, `_to_item`, `_to_option_item`, `_to_estimation_item`, `_build_alerts`, `_parse_percent`, and `_build_extreme` as module helpers. The class methods must use `user.id` and `uow.fund_favorites`, and all writes must call `uow.commit()`.

Use this class skeleton:

```python
from collections.abc import Callable

from app.core.current_user import CurrentUser
from app.db.models.fund_favorite import UserFavoriteFund


class FundFavoriteService:
    def __init__(self, uow_factory: Callable) -> None:
        self._uow_factory = uow_factory

    def add_favorite_fund(self, user: CurrentUser, payload: FavoriteFundAddRequest) -> FavoriteFundItem:
        fund_code = payload.fund_code.strip()
        fund_name = payload.fund_name.strip()
        fund_type = payload.fund_type.strip() if payload.fund_type else None

        with self._uow_factory() as uow:
            favorite = uow.fund_favorites.get_by_user_and_code(user.id, fund_code)
            if favorite is None:
                favorite = UserFavoriteFund(
                    user_id=user.id,
                    fund_code=fund_code,
                    fund_name=fund_name,
                    fund_type=fund_type,
                )
                uow.fund_favorites.add(favorite)
            else:
                favorite.fund_name = fund_name
                favorite.fund_type = fund_type

            uow.commit()
            uow.fund_favorites.refresh(favorite)
            return _to_item(favorite)
```

- [ ] **Step 7: Refactor fund and AI routes to injected services**

Modify fund favorite route handlers in `app/api/routes/fund/fund_view.py` so DB/current ORM imports are removed and favorite endpoints use:

```python
from app.api.dependencies import get_current_user_context, get_fund_favorite_service
from app.core.current_user import CurrentUser
from app.services.fund_favorite_service import FundFavoriteService
```

Example handler:

```python
def add_favorite_fund(
    request: Request,
    payload: FavoriteFundAddRequest,
    service: Annotated[FundFavoriteService, Depends(get_fund_favorite_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, service.add_favorite_fund(current_user, payload))
```

Modify report handlers and summary-save helper in `app/api/routes/ai/ai_view.py`:

```python
from app.api.dependencies import get_ai_fund_report_service, get_current_user_context
from app.core.current_user import CurrentUser
from app.services.ai_fund_report_service import AiFundReportService
```

`_to_sse_and_save` should accept `report_service: AiFundReportService` and call:

```python
report_service.create_report(current_user, fund_code, content)
```

- [ ] **Step 8: Run favorite and AI route tests**

Run: `uv run pytest tests/test_fund_favorite_routes.py tests/test_ai_routes.py -v`

Expected: PASS.

- [ ] **Step 9: Commit favorites and reports migration**

```bash
git add app/repositories/fund_favorites.py app/repositories/ai_fund_reports.py app/db/uow.py app/bootstrap.py app/api/dependencies.py app/services/fund_favorite_service.py app/services/ai_fund_report_service.py app/api/routes/fund/fund_view.py app/api/routes/ai/ai_view.py tests/test_fund_favorite_routes.py tests/test_ai_routes.py
git commit -m "refactor: migrate fund favorites and ai reports to uow"
```

---

### Task 4: Agent Service Migration and Streaming Session Lifetime

**Files:**
- Create: `app/repositories/agents.py`
- Modify: `app/db/uow.py`
- Modify: `app/bootstrap.py`
- Modify: `app/api/dependencies.py`
- Modify: `app/services/agent_service.py`
- Modify: `app/services/agent_runtime_service.py`
- Modify: `app/api/routes/agent/agent_view.py`
- Modify: `tests/test_agent_routes.py`

- [ ] **Step 1: Write failing agent streaming boundary test**

Add to `tests/test_agent_routes.py`:

```python
def test_stream_agent_chat_runtime_does_not_receive_live_db_session(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    def fake_stream_agent_chat(agent: AgentDefinition, payload: dict, history: list[dict], user, db):
        assert db is None
        yield message_event("可以先观望")

    monkeypatch.setattr(agent_runtime_service, "stream_agent_chat", fake_stream_agent_chat)

    client, _ = make_client_with_session()
    try:
        token = register_and_login(client)
        with client.stream(
            "POST",
            "/api/v1/agents/chat/stream",
            json={"agent_id": 1, "message": "今天怎么看？", "fund_code": "110010"},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = response.read().decode("utf-8")

        assert response.status_code == 200
        assert "可以先观望" in body
    finally:
        clear_overrides()
```

- [ ] **Step 2: Run new agent test to verify it fails**

Run: `uv run pytest tests/test_agent_routes.py::test_stream_agent_chat_runtime_does_not_receive_live_db_session -v`

Expected: FAIL because the current runtime receives the live `Session`.

- [ ] **Step 3: Implement agent repository**

Create `app/repositories/agents.py` with focused methods copied from current `agent_service.py` query/write logic:

```python
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.agent import AgentConversation, AgentDefinition, AgentMessage, AgentReport, AgentRun


class AgentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_definition_by_code(self, code: str) -> AgentDefinition | None:
        return self._session.scalar(select(AgentDefinition).where(AgentDefinition.code == code))

    def get_enabled_definition_for_user(self, agent_id: int, user_id: int) -> AgentDefinition | None:
        return self._session.scalar(
            select(AgentDefinition).where(
                AgentDefinition.id == agent_id,
                AgentDefinition.enabled.is_(True),
                or_(AgentDefinition.is_builtin.is_(True), AgentDefinition.owner_user_id == user_id),
            )
        )

    def add(self, value) -> None:
        self._session.add(value)

    def flush(self) -> None:
        self._session.flush()

    def refresh(self, value) -> None:
        self._session.refresh(value)
```

Add all list/detail helper methods needed by the existing service: `count_definitions_for_user`, `list_definitions_for_user`, `count_reports_for_user`, `list_reports_for_user`, `get_report_for_user`, `count_conversations_for_user_agent`, `list_conversations_for_user_agent`, `get_conversation_for_user`, `list_visible_messages`, `list_history_messages`, and `get_conversation_for_user_agent`.

- [ ] **Step 4: Extend UoW/bootstrap/dependencies for agent service**

Modify `app/db/uow.py`:

```python
from app.repositories.agents import AgentRepository
```

Inside `__enter__`:

```python
self.agents = AgentRepository(self._session)
```

Modify `app/bootstrap.py`:

```python
from app.services.agent_service import AgentService


def create_agent_service(uow_factory):
    return AgentService(uow_factory)
```

Modify `app/api/dependencies.py`:

```python
from app.services.agent_service import AgentService


def get_agent_service(
    uow_factory: Annotated[UowFactory, Depends(get_uow_factory)],
) -> AgentService:
    return create_agent_service(uow_factory)
```

- [ ] **Step 5: Refactor agent service into short UoW service class**

Modify `app/services/agent_service.py`:

- Keep `BUILTIN_AGENTS` and all `_to_*` mapper helpers.
- Add `AgentService`.
- Make list/detail methods use short `with self._uow_factory() as uow` scopes.
- Replace `HTTPException(status_code=404, detail=...)` with `NotFoundError(...)`.
- Replace bad message `HTTPException(status_code=400, detail="message is required")` with `ValidationError("message is required")`.
- Add `stream_chat` that:
  - Opens one UoW to ensure built-ins, load agent, create/load conversation, save user message, create run, build history DTOs, and commit.
  - Yields `conversation_event(conversation_id)`.
  - Calls `agent_runtime_service.stream_agent_chat(agent_snapshot, payload, history, user, None)`.
  - Persists tool messages with short UoW calls.
  - Persists final assistant message and run success with a short UoW.
  - Persists run failure with a short UoW and yields `error_event(str(exc))`.

Use a small dataclass snapshot for runtime input so no ORM object crosses the closed UoW:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentDefinitionDTO:
    id: int
    name: str
    code: str
    agent_type: str
    description: str
    system_prompt: str
    graph_code: str
```

- [ ] **Step 6: Allow runtime service to accept DTO and no DB session**

Modify `app/services/agent_runtime_service.py` type expectations so `agent` only needs `.graph_code` and `.code`, and `db` may be `None`. Keep existing behavior for graph functions that do not need DB in chat mode.

Do not pass DB into `stream_agent_chat_response`.

- [ ] **Step 7: Refactor agent routes**

Modify `app/api/routes/agent/agent_view.py`:

- Remove `Session`, `get_db`, and ORM `User` imports.
- Inject `AgentService` through `get_agent_service`.
- Inject `CurrentUser` through `get_current_user_context`.
- Call service methods with `current_user`.

Example:

```python
def list_agents(
    request: Request,
    payload: AgentListRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    current_user: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ApiResponse:
    return success_response(request, service.list_agents(current_user, page=payload.page, page_size=payload.page_size))
```

- [ ] **Step 8: Run agent tests**

Run: `uv run pytest tests/test_agent_routes.py -v`

Expected: PASS.

- [ ] **Step 9: Commit agent migration**

```bash
git add app/repositories/agents.py app/db/uow.py app/bootstrap.py app/api/dependencies.py app/services/agent_service.py app/services/agent_runtime_service.py app/api/routes/agent/agent_view.py tests/test_agent_routes.py
git commit -m "refactor: migrate agent service to short uow scopes"
```

---

### Task 5: Lifespan, Main, Compatibility, and Project Rules

**Files:**
- Create: `app/core/lifespan.py`
- Modify: `app/main.py`
- Modify: `agent.md`
- Modify: `tests/test_health_routes.py`

- [ ] **Step 1: Write failing lifespan startup-state test**

Add to `tests/test_health_routes.py`:

```python
def test_app_lifespan_sets_startup_complete_state():
    with TestClient(app) as client:
        response = client.get("/api/v1/health/startup")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "startup_complete": True,
    }
```

- [ ] **Step 2: Run lifespan test to verify it fails if state is not explicit**

Run: `uv run pytest tests/test_health_routes.py::test_app_lifespan_sets_startup_complete_state -v`

Expected: FAIL if lifespan does not set `startup_complete` explicitly.

- [ ] **Step 3: Implement lifespan module**

Create `app/core/lifespan.py`:

```python
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import FastAPI

from app.db.session import init_db


@contextmanager
def app_lifespan(app: FastAPI) -> Iterator[None]:
    app.state.startup_complete = False
    init_db()
    app.state.startup_complete = True
    try:
        yield
    finally:
        app.state.startup_complete = False
```

Modify `app/main.py`:

```python
from fastapi import FastAPI

from app.api.routes.agent.agent_view import router as agent_router
from app.api.routes.ai.ai_view import router as ai_router
from app.api.routes.fund.fund_view import router as fund_router
from app.api.routes.health.health_view import router as health_router
from app.api.routes.settings.settings_view import router as settings_router
from app.api.routes.user.user_view import router as user_router
from app.core.exception import register_exception_handlers
from app.core.lifespan import app_lifespan
from app.core.middleware import register_request_middleware

app = FastAPI(title="Surface API", lifespan=app_lifespan)
register_request_middleware(app)
register_exception_handlers(app)
app.include_router(health_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(fund_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
```

- [ ] **Step 4: Run lifespan and health tests**

Run: `uv run pytest tests/test_health_routes.py -v`

Expected: PASS.

- [ ] **Step 5: Update `agent.md` with Python backend rules**

Append to `agent.md`:

```markdown

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
```

- [ ] **Step 6: Commit lifespan and rules**

```bash
git add app/core/lifespan.py app/main.py agent.md tests/test_health_routes.py
git commit -m "docs: add backend development rules"
```

---

### Task 6: Full Verification and Refactor Cleanup

**Files:**
- Inspect/modify only files touched by Tasks 1-5 if verification reveals issues.

- [ ] **Step 1: Search for forbidden service-layer FastAPI exceptions**

Run: `rg -n "HTTPException|Request|Response|Depends\\(" app/services app/repositories`

Expected: no matches in `app/services` or `app/repositories`. If matches remain in service modules, replace them with application exceptions or injected collaborators.

- [ ] **Step 2: Search for repository commits**

Run: `rg -n "\\.commit\\(|\\.rollback\\(" app/repositories app/services`

Expected: repositories have no matches. Services may call `uow.commit()` only.

- [ ] **Step 3: Search for routers using raw DB sessions**

Run: `rg -n "Session|Depends\\(get_db\\)|get_db" app/api/routes app/core/security.py`

Expected: only `health_view.py` may use `get_db` for readiness compatibility. Other routers should use service dependencies and current-user context.

- [ ] **Step 4: Run backend test suite**

Run: `uv run pytest -v`

Expected: PASS.

- [ ] **Step 5: Commit cleanup if any code changed**

If fixes were needed:

```bash
git add app tests
git commit -m "refactor: clean up backend v1.2 boundaries"
```

If no fixes were needed, do not create an empty commit.

---

## Self-Review

- Spec coverage: Tasks cover composition root, dependency providers, UoW factory, repositories, service classes, domain exception mapping, DTO/current-user boundary, streaming short DB scopes, split health checks, `agent.md`, and verification.
- Placeholder scan: no task uses TBD/TODO or unspecified implementation-only instructions. Task 4 agent repository lists exact required methods but leaves copied query bodies to implementation because they are mechanical migrations from the existing service and must preserve current behavior.
- Type consistency: `CurrentUser`, `SqlAlchemyUnitOfWork`, service provider names, and route dependency names are defined before use.
