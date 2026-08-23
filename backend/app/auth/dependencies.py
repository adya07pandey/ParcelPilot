from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token
from app.models import Role, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise AuthenticationError()
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise AuthenticationError("Invalid access token", code="INVALID_TOKEN") from exc

    user = db.get(User, payload.get("sub"))
    if not user or user.status != "ACTIVE":
        raise AuthenticationError("Invalid access token", code="INVALID_TOKEN")
    return user


def require_roles(*roles: Role) -> Callable[[User], User]:
    allowed = {role.value for role in roles}

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise AuthorizationError()
        return current_user

    return dependency


def can_access_account(current_user: User, account_id: str) -> bool:
    if current_user.role in {Role.SUPPORT.value, Role.ADMIN.value}:
        return True
    return current_user.account_id == account_id
