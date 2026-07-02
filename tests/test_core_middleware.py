from fastapi.testclient import TestClient

from app.api.dependencies import get_current_user_context
from app.core.current_user import CurrentUser
from app.main import app


def test_request_middleware_adds_request_id_and_process_time_headers():
    request_id = "test-request-id"

    response = TestClient(app).get("/api/v1/funds/not-exist", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id
    assert "X-Process-Time" in response.headers


def test_http_exception_response_uses_standard_error_shape():
    app.dependency_overrides[get_current_user_context] = lambda: CurrentUser(id=1, username="admin")
    try:
        response = TestClient(app).post("/api/v1/funds/value", json={"fund_code": "", "source": "daily"})
    finally:
        app.dependency_overrides.pop(get_current_user_context, None)

    assert response.status_code == 400
    assert response.json() == {
        "code": 400,
        "message": "fund_code is required",
        "data": None,
        "request_id": response.headers["X-Request-ID"],
    }


def test_fund_routes_require_token():
    response = TestClient(app).post("/api/v1/funds/list", json={"page": 1, "page_size": 10})

    assert response.status_code == 401
    assert response.json()["code"] == 401
