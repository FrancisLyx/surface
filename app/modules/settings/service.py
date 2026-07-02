from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db.uow import SqlAlchemyUnitOfWork


class SystemSettingService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def get_registration_setting(self) -> dict[str, bool]:
        with self._uow_factory() as uow:
            return {"enabled": uow.system_settings.is_registration_enabled()}

    def update_registration_setting(self, enabled: bool) -> dict[str, bool]:
        with self._uow_factory() as uow:
            uow.system_settings.set_registration_enabled(enabled)
            uow.commit()
            return {"enabled": enabled}


def _service_from_session(db: Session) -> SystemSettingService:
    return SystemSettingService(lambda: SqlAlchemyUnitOfWork(lambda: db))


def get_registration_setting(db: Session) -> dict[str, bool]:
    return _service_from_session(db).get_registration_setting()


def update_registration_setting(db: Session, enabled: bool) -> dict[str, bool]:
    return _service_from_session(db).update_registration_setting(enabled)


def is_user_registration_enabled(db: Session) -> bool:
    with SqlAlchemyUnitOfWork(lambda: db) as uow:
        return uow.system_settings.is_registration_enabled()
