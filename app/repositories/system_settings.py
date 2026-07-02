from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import is_user_registration_enabled as get_env_registration_enabled
from app.db.models.system_setting import SystemSetting

USER_REGISTRATION_ENABLED_KEY = "user_registration_enabled"


class SystemSettingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def is_registration_enabled(self) -> bool:
        setting = self._session.scalar(select(SystemSetting).where(SystemSetting.key == USER_REGISTRATION_ENABLED_KEY))
        if setting is None:
            return get_env_registration_enabled()
        return _setting_value_to_bool(setting.value)

    def set_registration_enabled(self, enabled: bool) -> None:
        setting = self._session.get(SystemSetting, USER_REGISTRATION_ENABLED_KEY)
        if setting is None:
            setting = SystemSetting(key=USER_REGISTRATION_ENABLED_KEY, value=_bool_to_setting_value(enabled))
            self._session.add(setting)
        else:
            setting.value = _bool_to_setting_value(enabled)


def _bool_to_setting_value(value: bool) -> str:
    return "true" if value else "false"


def _setting_value_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
