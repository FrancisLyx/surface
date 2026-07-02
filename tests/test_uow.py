import pytest

from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.user.uow import UserUnitOfWork


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def close(self):
        self.closes += 1


@pytest.mark.asyncio
async def test_uow_rolls_back_and_closes_when_not_committed():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    async with uow:
        assert uow.session is session

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


@pytest.mark.asyncio
async def test_uow_commits_explicitly_and_closes_without_rollback():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    async with uow:
        await uow.commit()

    assert session.commits == 1
    assert session.rollbacks == 0
    assert session.closes == 1


@pytest.mark.asyncio
async def test_uow_rolls_back_exception_even_after_no_commit():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with pytest.raises(RuntimeError, match="boom"):
        async with uow:
            raise RuntimeError("boom")

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


def test_uow_rejects_session_access_outside_context():
    uow = SqlAlchemyUnitOfWork(lambda: FakeSession())

    with pytest.raises(RuntimeError, match="Unit of Work is not active"):
        _ = uow.session


@pytest.mark.asyncio
async def test_base_uow_does_not_attach_module_repositories():
    uow = SqlAlchemyUnitOfWork(lambda: FakeSession())

    async with uow:
        assert not hasattr(uow, "users")
        assert not hasattr(uow, "system_settings")
        assert not hasattr(uow, "fund_favorites")
        assert not hasattr(uow, "ai_fund_reports")
        assert not hasattr(uow, "agents")


@pytest.mark.asyncio
async def test_module_uow_attaches_only_its_module_repositories():
    uow = UserUnitOfWork(lambda: FakeSession())

    async with uow:
        assert hasattr(uow, "users")
        assert not hasattr(uow, "fund_favorites")
        assert not hasattr(uow, "ai_fund_reports")
        assert not hasattr(uow, "agents")
