from fastapi.testclient import TestClient

from app.core.readiness import ReadinessState
from app.infrastructure.database import session as db_session
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
        async def execute(self, statement):
            return FakeScalarResult()

        async def close(self):
            pass

    async def fake_get_db():
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
    assert app.state.readiness.snapshot()["dependencies"]["database"]["status"] == "ok"


def test_health_alias_reports_readiness():
    class FakeScalarResult:
        def scalar_one(self):
            return 1

    class FakeSession:
        async def execute(self, statement):
            return FakeScalarResult()

        async def close(self):
            pass

    async def fake_get_db():
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


def test_app_lifespan_sets_startup_complete_state():
    if hasattr(app.state, "startup_complete"):
        delattr(app.state, "startup_complete")

    with TestClient(app) as client:
        assert hasattr(app.state, "startup_complete")
        response = client.get("/api/v1/health/startup")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "startup_complete": True,
    }


def test_readiness_state_tracks_dependency_failures():
    state = ReadinessState()
    state.mark_ok("database")
    assert state.is_ready() is True

    state.mark_failed("database", "connection refused")

    snapshot = state.snapshot()
    assert state.is_ready() is False
    assert snapshot["status"] == "degraded"
    assert snapshot["dependencies"]["database"] == {
        "status": "failed",
        "message": "connection refused",
    }
