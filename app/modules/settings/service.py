from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.uow import SettingsUnitOfWork


class SystemSettingService:
    def __init__(self, uow_factory: Callable[[], SettingsUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def get_registration_setting(self) -> dict[str, bool]:
        async with self._uow_factory() as uow:
            return {"enabled": await uow.system_settings.is_registration_enabled()}

    async def update_registration_setting(self, enabled: bool) -> dict[str, bool]:
        async with self._uow_factory() as uow:
            await uow.system_settings.set_registration_enabled(enabled)
            await uow.commit()
            return {"enabled": enabled}


def _service_from_session(db: AsyncSession) -> SystemSettingService:
    return SystemSettingService(lambda: SettingsUnitOfWork(lambda: db))


async def get_registration_setting(db: AsyncSession) -> dict[str, bool]:
    return await _service_from_session(db).get_registration_setting()


async def update_registration_setting(
    db: AsyncSession, enabled: bool
) -> dict[str, bool]:
    return await _service_from_session(db).update_registration_setting(enabled)


async def is_user_registration_enabled(db: AsyncSession) -> bool:
    async with SettingsUnitOfWork(lambda: db) as uow:
        return await uow.system_settings.is_registration_enabled()
