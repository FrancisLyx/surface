from fastapi import Depends

from app.core.security import get_current_user


def require_auth():
    return Depends(get_current_user)
