from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import dependencies
from app.core.current_user import CurrentUser
from app.core.exception import NotFoundError
from app.db import session as db_session
from app.db.base import Base
from app.modules.ai.report_model import AiFundReport
from app.db.uow import SqlAlchemyUnitOfWork
from app.main import app
from app.modules.ai import service as ai_fund_service


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
    app.dependency_overrides[dependencies.get_uow_factory] = lambda: lambda: SqlAlchemyUnitOfWork(TestingSessionLocal)
    return TestClient(app)


def make_client_with_session():
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
    return TestClient(app), TestingSessionLocal


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def register_and_login(client: TestClient) -> str:
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

    login_response = client.post(
        "/api/v1/user/login",
        json={"account": "admin", "password": "123456"},
    )
    assert login_response.status_code == 200
    return login_response.json()["data"]["access_token"]


def test_ai_report_service_returns_not_found_for_other_user():
    from app.modules.ai.report_service import AiFundReportService

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


def test_stream_fund_summary_requires_token():
    response = TestClient(app).post("/api/v1/ai/funds/summary/stream", json={"fund_code": "110010"})

    assert response.status_code == 401


def test_stream_fund_summary_returns_sse(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    def fake_stream_fund_summary(fund_code: str):
        assert fund_code == "110010"
        yield "第一段"
        yield "第二段"

    monkeypatch.setattr(ai_fund_service, "stream_fund_summary", fake_stream_fund_summary)

    client = make_client()
    try:
        token = register_and_login(client)
        with client.stream(
            "POST",
            "/api/v1/ai/funds/summary/stream",
            json={"fund_code": "110010"},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = response.read().decode("utf-8")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "data: 第一段\n\n" in body
        assert "data: 第二段\n\n" in body
        assert "event: done\ndata: [DONE]\n\n" in body
    finally:
        clear_overrides()


def test_stream_fund_summary_saves_completed_report(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    def fake_stream_fund_summary(fund_code: str):
        assert fund_code == "110010"
        yield "# 当日操作建议\n"
        yield "动作结论：观望"

    monkeypatch.setattr(ai_fund_service, "stream_fund_summary", fake_stream_fund_summary)

    client, TestingSessionLocal = make_client_with_session()
    try:
        token = register_and_login(client)
        with client.stream(
            "POST",
            "/api/v1/ai/funds/summary/stream",
            json={"fund_code": "110010"},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = response.read().decode("utf-8")

        assert response.status_code == 200
        assert "event: done\ndata: [DONE]\n\n" in body

        db = TestingSessionLocal()
        try:
            reports = db.query(AiFundReport).all()
            assert len(reports) == 1
            assert reports[0].user_id == 1
            assert reports[0].fund_code == "110010"
            assert reports[0].content == "# 当日操作建议\n动作结论：观望"
            assert reports[0].created_at is not None
        finally:
            db.close()
    finally:
        clear_overrides()


def test_list_and_get_fund_reports_are_scoped_to_current_user(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client, TestingSessionLocal = make_client_with_session()
    try:
        admin_token = register_and_login(client)
        guest_register_response = client.post(
            "/api/v1/user/register",
            json={
                "username": "guest",
                "email": "guest@example.com",
                "phone": "13900139000",
                "password": "123456",
            },
        )
        assert guest_register_response.status_code == 200
        guest_login_response = client.post(
            "/api/v1/user/login",
            json={"account": "guest", "password": "123456"},
        )
        assert guest_login_response.status_code == 200
        guest_token = guest_login_response.json()["data"]["access_token"]

        db = TestingSessionLocal()
        try:
            from app.modules.ai.report_model import AiFundReport

            db.add_all(
                [
                    AiFundReport(user_id=1, fund_code="110010", content="# admin report"),
                    AiFundReport(user_id=2, fund_code="000001", content="# guest report"),
                ]
            )
            db.commit()
        finally:
            db.close()

        list_response = client.post(
            "/api/v1/ai/funds/reports/list",
            json={"page": 1, "page_size": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert list_response.status_code == 200
        assert list_response.json()["data"]["total"] == 1
        admin_report = list_response.json()["data"]["items"][0]
        assert admin_report["fund_code"] == "110010"
        assert admin_report["created_at"]
        assert "content" not in admin_report

        detail_response = client.post(
            "/api/v1/ai/funds/reports/detail",
            json={"id": admin_report["id"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["content"] == "# admin report"

        forbidden_detail_response = client.post(
            "/api/v1/ai/funds/reports/detail",
            json={"id": admin_report["id"]},
            headers={"Authorization": f"Bearer {guest_token}"},
        )
        assert forbidden_detail_response.status_code == 404
    finally:
        clear_overrides()
