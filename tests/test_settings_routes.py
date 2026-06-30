from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import session as db_session
from app.db.base import Base
from app.main import app


def make_client() -> TestClient:
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
    return TestClient(app)


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, username: str = "admin") -> str:
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "phone": "13800138000" if username == "admin" else "13900139000",
            "password": "123456",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/v1/user/login",
        json={"account": username, "password": "123456"},
    )
    assert login_response.status_code == 200
    return login_response.json()["data"]["access_token"]


def test_update_registration_setting_requires_token():
    response = TestClient(app).post(
        "/api/v1/settings/registration",
        json={"enabled": False},
    )

    assert response.status_code == 401


def test_update_registration_setting_controls_register_flow(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = make_client()
    try:
        token = register_and_login(client)

        close_response = client.post(
            "/api/v1/settings/registration",
            json={"enabled": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert close_response.status_code == 200
        assert close_response.json()["data"] == {"enabled": False}

        status_response = client.get("/api/v1/user/register-status")
        assert status_response.status_code == 200
        assert status_response.json()["data"] == {"enabled": False}

        disabled_register_response = client.post(
            "/api/v1/user/register",
            json={
                "username": "guest",
                "email": "guest@example.com",
                "phone": "13900139000",
                "password": "123456",
            },
        )
        assert disabled_register_response.status_code == 403
        assert disabled_register_response.json()["message"] == "registration is disabled"

        open_response = client.post(
            "/api/v1/settings/registration",
            json={"enabled": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert open_response.status_code == 200
        assert open_response.json()["data"] == {"enabled": True}

        enabled_register_response = client.post(
            "/api/v1/user/register",
            json={
                "username": "guest",
                "email": "guest@example.com",
                "phone": "13900139000",
                "password": "123456",
            },
        )
        assert enabled_register_response.status_code == 200
    finally:
        clear_overrides()
