import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import dependencies
from app.api.routes.user.user_schema import UserRegisterRequest
from app.db import session as db_session
from app.db.base import Base
from app.db.uow import SqlAlchemyUnitOfWork
from app.main import app


def with_test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session.get_db] = override_db
    app.dependency_overrides[dependencies.get_uow_factory] = lambda: lambda: SqlAlchemyUnitOfWork(TestingSessionLocal)
    return TestClient(app)


def clear_overrides():
    app.dependency_overrides.clear()


def test_register_status_returns_feature_switch(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "false")

    response = TestClient(app).get("/api/v1/user/register-status")

    assert response.status_code == 200
    assert response.json()["data"] == {"enabled": False}


def test_register_login_and_me_flow(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = with_test_db()
    try:
        register_response = client.post(
            "/api/v1/user/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "phone": "13800138000",
                "password": "123456",
            },
        )
        assert register_response.status_code == 200
        assert register_response.json()["data"]["username"] == "admin"
        assert register_response.json()["data"]["email"] == "admin@example.com"
        assert register_response.json()["data"]["phone"] == "13800138000"

        login_response = client.post(
            "/api/v1/user/login",
            json={"account": "admin@example.com", "password": "123456"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]
        assert login_response.json()["data"]["token_type"] == "bearer"

        me_response = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})
        assert me_response.status_code == 200
        assert me_response.json()["data"] == {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "phone": "13800138000",
        }
    finally:
        clear_overrides()


def test_register_rejects_duplicate_username(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = with_test_db()
    payload = {
        "username": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "password": "123456",
    }
    try:
        assert client.post("/api/v1/user/register", json=payload).status_code == 200
        response = client.post(
            "/api/v1/user/register",
            json={**payload, "email": "other@example.com", "phone": "13900139000"},
        )

        assert response.status_code == 400
        assert response.json()["message"] == "username already exists"
    finally:
        clear_overrides()


def test_register_can_be_disabled(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "false")
    client = with_test_db()
    try:
        response = client.post(
            "/api/v1/user/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "phone": "13800138000",
                "password": "123456",
            },
        )

        assert response.status_code == 403
        assert response.json()["message"] == "registration is disabled"
    finally:
        clear_overrides()


def test_login_rejects_wrong_password(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = with_test_db()
    try:
        client.post(
            "/api/v1/user/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "phone": "13800138000",
                "password": "123456",
            },
        )
        response = client.post(
            "/api/v1/user/login",
            json={"account": "admin", "password": "bad-password"},
        )

        assert response.status_code == 401
        assert response.json()["message"] == "invalid account or password"
    finally:
        clear_overrides()


def test_me_requires_token():
    response = TestClient(app).get("/api/v1/user/me")

    assert response.status_code == 401


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
