from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import is_user_registration_enabled as get_env_registration_enabled
from app.db.models.system_setting import SystemSetting

USER_REGISTRATION_ENABLED_KEY = "user_registration_enabled"


def get_registration_setting(db: Session) -> dict[str, bool]:
    return {"enabled": is_user_registration_enabled(db)}


def update_registration_setting(db: Session, enabled: bool) -> dict[str, bool]:
    setting = db.get(SystemSetting, USER_REGISTRATION_ENABLED_KEY)
    if setting is None:
        setting = SystemSetting(key=USER_REGISTRATION_ENABLED_KEY, value=_bool_to_setting_value(enabled))
        db.add(setting)
    else:
        setting.value = _bool_to_setting_value(enabled)

    db.commit()
    return {"enabled": enabled}


def is_user_registration_enabled(db: Session) -> bool:
    setting = db.scalar(select(SystemSetting).where(SystemSetting.key == USER_REGISTRATION_ENABLED_KEY))
    if setting is None:
        return get_env_registration_enabled()
    return _setting_value_to_bool(setting.value)


def _bool_to_setting_value(value: bool) -> str:
    return "true" if value else "false"


def _setting_value_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
