from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppException(40100, "Not authenticated", 401)
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, int(user_id)) if str(user_id).isdigit() else None
    if user is None or not user.is_active:
        raise AppException(40100, "User not found or disabled", 401)
    return user


def get_user_permissions(user: User) -> set[str]:
    if user.is_superuser:
        return {permission.code for role in user.roles for permission in role.permissions}
    return {permission.code for role in user.roles for permission in role.permissions}


def require_permission(permission_code: str) -> Callable:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        permissions = get_user_permissions(current_user)
        if permission_code not in permissions and not current_user.is_superuser:
            raise AppException(40300, "Permission denied", 403)
        return current_user

    return dependency
