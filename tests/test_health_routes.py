from fastapi.testclient import TestClient

from app.db import session as db_session
from app.main import app


def test_health_endpoint_reports_database_ok(monkeypatch):
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
    assert response.json()["code"] == 200
    assert response.json()["data"] == {
        "status": "ok",
        "database": "ok",
    }
