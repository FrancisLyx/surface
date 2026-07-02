import pytest

from app.db.uow import SqlAlchemyUnitOfWork


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closes += 1


def test_uow_rolls_back_and_closes_when_not_committed():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with uow:
        assert uow.session is session

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


def test_uow_commits_explicitly_and_closes_without_rollback():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with uow:
        uow.commit()

    assert session.commits == 1
    assert session.rollbacks == 0
    assert session.closes == 1


def test_uow_rolls_back_exception_even_after_no_commit():
    session = FakeSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)

    with pytest.raises(RuntimeError, match="boom"):
        with uow:
            raise RuntimeError("boom")

    assert session.commits == 0
    assert session.rollbacks == 1
    assert session.closes == 1


def test_uow_rejects_session_access_outside_context():
    uow = SqlAlchemyUnitOfWork(lambda: FakeSession())

    with pytest.raises(RuntimeError, match="Unit of Work is not active"):
        _ = uow.session
