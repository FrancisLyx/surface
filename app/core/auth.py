from fastapi import Depends

from app.api.dependencies import get_current_user_context


def require_auth():
    return Depends(get_current_user_context)
