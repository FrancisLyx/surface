from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import dependencies
from app.api.routes.fund.fund_schema import FavoriteFundAddRequest
from app.core.current_user import CurrentUser
from app.db import session as db_session
from app.db.base import Base
from app.db.uow import SqlAlchemyUnitOfWork
from app.main import app
from app.clients import akshare_client


class EmptyDailyNavData:
    def fillna(self, value):
        return self

    @property
    def columns(self):
        return ["基金代码", "基金简称"]

    def iterrows(self):
        yield from enumerate([])


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


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_favorite_service_accepts_current_user_context():
    from app.services.fund_favorite_service import FundFavoriteService

    class FakeFavorite:
        id = None
        user_id = None
        fund_code = ""
        fund_name = ""
        fund_type = None
        created_at = None

        def __init__(self, user_id: int, fund_code: str, fund_name: str, fund_type: str | None):
            self.user_id = user_id
            self.fund_code = fund_code
            self.fund_name = fund_name
            self.fund_type = fund_type

    class FakeFavorites:
        def __init__(self):
            self.added_user_id = None

        def get_by_user_and_code(self, user_id, fund_code):
            return None

        def add(self, favorite):
            self.added_user_id = favorite.user_id

        def refresh(self, favorite):
            from datetime import datetime

            favorite.id = 10
            favorite.created_at = datetime(2026, 1, 1)

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
    service = FundFavoriteService(lambda: uow, favorite_model=FakeFavorite)
    result = service.add_favorite_fund(
        CurrentUser(id=7, username="admin"),
        FavoriteFundAddRequest(fund_code="000001", fund_name="华夏成长混合", fund_type="混合型"),
    )

    assert uow.fund_favorites.added_user_id == 7
    assert uow.committed is True
    assert result.fund_code == "000001"


def register_and_login(client: TestClient, username: str, email: str, phone: str) -> str:
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "username": username,
            "email": email,
            "phone": phone,
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


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_add_list_and_remove_favorite_fund(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = make_client()
    try:
        token = register_and_login(client, "admin", "admin@example.com", "13800138000")

        add_response = client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(token),
        )

        assert add_response.status_code == 200
        assert add_response.json()["data"]["fund_code"] == "000001"
        assert add_response.json()["data"]["fund_name"] == "华夏成长混合"

        duplicate_response = client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(token),
        )

        assert duplicate_response.status_code == 200
        assert duplicate_response.json()["data"]["fund_code"] == "000001"

        list_response = client.post(
            "/api/v1/funds/favorites/list",
            json={"keyword": "华夏", "page": 1, "page_size": 10},
            headers=auth_headers(token),
        )

        assert list_response.status_code == 200
        assert list_response.json()["data"]["total"] == 1
        assert list_response.json()["data"]["items"][0]["fund_code"] == "000001"

        check_response = client.post(
            "/api/v1/funds/favorites/check",
            json={"fund_code": "000001"},
            headers=auth_headers(token),
        )

        assert check_response.status_code == 200
        assert check_response.json()["data"] == {"favorited": True}

        remove_response = client.post(
            "/api/v1/funds/favorites/remove",
            json={"fund_code": "000001"},
            headers=auth_headers(token),
        )

        assert remove_response.status_code == 200
        assert remove_response.json()["data"] == {"removed": True}

        empty_response = client.post(
            "/api/v1/funds/favorites/list",
            json={"page": 1, "page_size": 10},
            headers=auth_headers(token),
        )

        assert empty_response.status_code == 200
        assert empty_response.json()["data"]["total"] == 0
    finally:
        clear_overrides()


def test_favorite_funds_are_scoped_to_current_user(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = make_client()
    try:
        admin_token = register_and_login(client, "admin", "admin@example.com", "13800138000")
        guest_token = register_and_login(client, "guest", "guest@example.com", "13900139000")

        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(admin_token),
        )

        guest_list_response = client.post(
            "/api/v1/funds/favorites/list",
            json={"page": 1, "page_size": 10},
            headers=auth_headers(guest_token),
        )

        assert guest_list_response.status_code == 200
        assert guest_list_response.json()["data"]["total"] == 0
    finally:
        clear_overrides()


def test_list_favorite_fund_options_are_scoped_to_current_user(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client = make_client()
    try:
        admin_token = register_and_login(client, "admin", "admin@example.com", "13800138000")
        guest_token = register_and_login(client, "guest", "guest@example.com", "13900139000")

        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(admin_token),
        )
        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000002", "fund_name": "嘉实增长混合", "fund_type": "混合型-偏股"},
            headers=auth_headers(admin_token),
        )
        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000003", "fund_name": "中海可转债债券A", "fund_type": "债券型"},
            headers=auth_headers(guest_token),
        )

        response = client.post(
            "/api/v1/funds/favorites/options",
            headers=auth_headers(admin_token),
        )

        assert response.status_code == 200
        assert response.json()["data"] == [
            {
                "fund_code": "000002",
                "fund_name": "嘉实增长混合",
                "fund_type": "混合型-偏股",
            },
            {
                "fund_code": "000001",
                "fund_name": "华夏成长混合",
                "fund_type": "混合型-灵活",
            },
        ]
    finally:
        clear_overrides()


def test_list_favorite_fund_estimations(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    monkeypatch.setattr(
        akshare_client,
        "get_fund_realtime_estimation",
        lambda symbol: {
            "fundcode": "000001",
            "name": "华夏成长混合",
            "jzrq": "2026-06-28",
            "dwjz": "1.2200",
            "gsz": "1.2345",
            "gszzl": "1.23",
            "gztime": "2026-06-29 14:30",
        },
        raising=False,
    )
    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": (_ for _ in ()).throw(
            AssertionError("full estimation list should not be loaded for favorite estimations")
        ),
    )

    client = make_client()
    try:
        token = register_and_login(client, "admin", "admin@example.com", "13800138000")
        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(token),
        )

        response = client.post(
            "/api/v1/funds/favorites/estimations",
            json={"keyword": "华夏", "page": 1, "page_size": 10},
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        assert response.json()["data"]["total"] == 1
        assert response.json()["data"]["items"][0] == {
            "id": 1,
            "fund_code": "000001",
            "fund_name": "华夏成长混合",
            "fund_type": "混合型-灵活",
            "created_at": response.json()["data"]["items"][0]["created_at"],
            "estimate_date": "2026-06-29",
            "estimated_nav": "1.2345",
            "estimated_growth_rate": "1.23%",
            "published_date": "2026-06-28",
            "published_nav": "1.2200",
            "published_growth_rate": "",
            "estimate_deviation": "",
            "previous_nav_date": "2026-06-28",
            "previous_nav": "1.2200",
            "has_estimation": True,
        }
    finally:
        clear_overrides()


def test_get_favorite_fund_report(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    realtime_data = {
        "000001": {
            "fundcode": "000001",
            "name": "华夏成长混合",
            "jzrq": "2026-06-29",
            "dwjz": "1.2200",
            "gsz": "1.2345",
            "gszzl": "3.20",
            "gztime": "2026-06-30 14:30",
        },
        "000003": {
            "fundcode": "000003",
            "name": "中海可转债债券A",
            "jzrq": "2026-06-29",
            "dwjz": "1.0000",
            "gsz": "0.9800",
            "gszzl": "-2.10",
            "gztime": "2026-06-30 14:30",
        },
    }

    monkeypatch.setattr(
        akshare_client,
        "get_fund_realtime_estimation",
        lambda symbol: realtime_data[symbol],
        raising=False,
    )
    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": (_ for _ in ()).throw(
            AssertionError("full estimation list should not be loaded for favorite report")
        ),
    )

    client = make_client()
    try:
        token = register_and_login(client, "admin", "admin@example.com", "13800138000")
        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000001", "fund_name": "华夏成长混合", "fund_type": "混合型-灵活"},
            headers=auth_headers(token),
        )
        client.post(
            "/api/v1/funds/favorites/add",
            json={"fund_code": "000003", "fund_name": "中海可转债债券A", "fund_type": "债券型"},
            headers=auth_headers(token),
        )

        response = client.post(
            "/api/v1/funds/favorites/report",
            json={"page": 1, "page_size": 10},
            headers=auth_headers(token),
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["summary"] == {
            "total": 2,
            "estimated_count": 2,
            "up_count": 1,
            "down_count": 1,
            "flat_count": 0,
            "missing_count": 0,
            "alert_count": 2,
            "max_up": {"fund_code": "000001", "fund_name": "华夏成长混合", "rate": "3.20%"},
            "max_down": {"fund_code": "000003", "fund_name": "中海可转债债券A", "rate": "-2.10%"},
        }
        assert sorted(data["alerts"], key=lambda item: (item["fund_code"], item["message"])) == sorted([
            {
                "fund_code": "000001",
                "fund_name": "华夏成长混合",
                "level": "warning",
                "message": "估算涨幅 3.20%",
            },
            {
                "fund_code": "000003",
                "fund_name": "中海可转债债券A",
                "level": "warning",
                "message": "估算跌幅 -2.10%",
            },
        ], key=lambda item: (item["fund_code"], item["message"]))
    finally:
        clear_overrides()
