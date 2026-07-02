from fastapi.testclient import TestClient

from app.main import app
from tests.db_helpers import make_test_client


def make_client() -> TestClient:
    client, _ = make_test_client()
    return client


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
        assert (
            disabled_register_response.json()["message"] == "registration is disabled"
        )

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
