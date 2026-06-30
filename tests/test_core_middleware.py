from fastapi.testclient import TestClient

from app.main import app


def test_request_middleware_adds_request_id_and_process_time_headers():
    request_id = "test-request-id"

    response = TestClient(app).get("/funds/not-exist", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id
    assert "X-Process-Time" in response.headers


def test_http_exception_response_uses_standard_error_shape():
    response = TestClient(app).post("/funds/value", json={"fund_code": "", "source": "daily"})

    assert response.status_code == 400
    assert response.json() == {
        "code": 400,
        "message": "fund_code is required",
        "data": None,
        "request_id": response.headers["X-Request-ID"],
    }
