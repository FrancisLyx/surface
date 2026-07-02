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
