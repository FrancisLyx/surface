from collections.abc import Callable

from app.modules.settings.uow import SettingsUnitOfWork


class RegistrationPolicy:
    def __init__(self, uow_factory: Callable[[], SettingsUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def is_registration_enabled(self) -> bool:
        async with self._uow_factory() as uow:
            return await uow.system_settings.is_registration_enabled()
