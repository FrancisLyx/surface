from fastapi.testclient import TestClient
from app.services.agent_event import message_event
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import session as db_session
from app.db.base import Base
from app.db.models.agent import AgentConversation, AgentDefinition, AgentMessage, AgentReport, AgentRun
from app.main import app
from app.services import agent_runtime_service, agent_service


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
    return TestClient(app), TestingSessionLocal


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, username: str = "admin", email: str = "admin@example.com") -> str:
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "username": username,
            "email": email,
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


def test_list_agents_returns_enabled_builtin_agents(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client, _ = make_client_with_session()
    try:
        token = register_and_login(client)

        response = client.post(
            "/api/v1/agents/list",
            json={"page": 1, "page_size": 10},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 3
        names = {item["name"] for item in data["items"]}
        assert names == {"林远山", "许知夏", "股神阿佳"}
        assert all("code" not in item for item in data["items"])
        assert all(item["enabled"] for item in data["items"])
    finally:
        clear_overrides()


def test_stream_agent_chat_saves_conversation_and_messages(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")

    def fake_stream_agent_chat(agent: AgentDefinition, payload: dict, history: list[dict], user, db):
        assert agent.code == "fund_deep_analysis"
        assert payload == {"message": "今天怎么看？", "fund_code": "110010"}
        assert history == []
        yield message_event("可以先观望")

    monkeypatch.setattr(agent_runtime_service, "stream_agent_chat", fake_stream_agent_chat)

    client, TestingSessionLocal = make_client_with_session()
    try:
        token = register_and_login(client)
        with client.stream(
            "POST",
            "/api/v1/agents/chat/stream",
            json={"agent_id": 1, "message": "今天怎么看？", "fund_code": "110010"},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = response.read().decode("utf-8")

        assert response.status_code == 200
        assert 'event: conversation\ndata: {"type":"conversation","conversation_id":1}\n\n' in body
        assert 'event: message\ndata: {"type":"assistant_delta","content":"可以先观望"}\n\n' in body

        list_response = client.post(
            "/api/v1/agents/conversations/list",
            json={"agent_id": 1, "page": 1, "page_size": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        conversation = list_response.json()["data"]["items"][0]
        assert conversation["id"] == 1
        assert conversation["title"] == "今天怎么看？"
        assert conversation["target_code"] == "110010"

        detail_response = client.post(
            "/api/v1/agents/conversations/detail",
            json={"conversation_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()["data"]
        assert detail["id"] == 1
        assert [item["role"] for item in detail["messages"]] == ["user", "assistant"]
        assert [item["content"] for item in detail["messages"]] == ["今天怎么看？", "可以先观望"]

        db = TestingSessionLocal()
        try:
            conversations = db.query(AgentConversation).all()
            messages = db.query(AgentMessage).order_by(AgentMessage.id.asc()).all()
            runs = db.query(AgentRun).all()
            assert len(conversations) == 1
            assert conversations[0].target_code == "110010"
            assert [item.role for item in messages] == ["user", "assistant"]
            assert messages[0].content == "今天怎么看？"
            assert messages[1].content == "可以先观望"
            assert len(runs) == 1
            assert runs[0].conversation_id == conversations[0].id
            assert runs[0].output_text == "可以先观望"
        finally:
            db.close()
    finally:
        clear_overrides()


def test_agent_reports_are_scoped_to_current_user(monkeypatch):
    monkeypatch.setenv("USER_REGISTRATION_ENABLED", "true")
    client, TestingSessionLocal = make_client_with_session()
    try:
        admin_token = register_and_login(client)
        guest_token = register_and_login(client, username="guest", email="guest@example.com")

        db = TestingSessionLocal()
        try:
            agent_service.ensure_builtin_agents(db)
            admin_agent = db.query(AgentDefinition).filter_by(code="fund_deep_analysis").one()
            admin_agent_id = admin_agent.id
            run = AgentRun(
                user_id=1,
                agent_id=admin_agent.id,
                input_json={"fund_code": "110010"},
                output_text="# admin report",
                status="success",
            )
            db.add(run)
            db.flush()
            db.add(
                AgentReport(
                    user_id=1,
                    agent_id=admin_agent.id,
                    run_id=run.id,
                    title="110010 基金深度分析",
                    target_type="fund",
                    target_code="110010",
                    content="# admin report",
                )
            )
            db.commit()
        finally:
            db.close()

        list_response = client.post(
            "/api/v1/agents/reports/list",
            json={"page": 1, "page_size": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["data"]["total"] == 1
        report = list_response.json()["data"]["items"][0]
        assert report["target_code"] == "110010"
        assert report["agent_id"] == admin_agent_id
        assert "agent_code" not in report
        assert "content" not in report

        detail_response = client.post(
            "/api/v1/agents/reports/detail",
            json={"id": report["id"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["data"]["content"] == "# admin report"

        forbidden_response = client.post(
            "/api/v1/agents/reports/detail",
            json={"id": report["id"]},
            headers={"Authorization": f"Bearer {guest_token}"},
        )
        assert forbidden_response.status_code == 404
    finally:
        clear_overrides()
