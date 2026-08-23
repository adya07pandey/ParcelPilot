import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.schemas import AuthResponse, user_response
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, hash_token, verify_password
from app.models import RefreshToken, User


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or user.status != "ACTIVE" or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")
    user.last_login_at = datetime.now(timezone.utc)
    return user


def issue_refresh_token(db: Session, user: User) -> tuple[str, RefreshToken]:
    settings = get_settings()
    raw_token = create_refresh_token()
    now = datetime.now(timezone.utc)
    record = RefreshToken(
        id=f"rt_{secrets.token_urlsafe(16)}",
        user_id=user.user_id,
        token_hash=hash_token(raw_token),
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    db.add(record)
    return raw_token, record


def issue_auth_response(db: Session, user: User) -> tuple[AuthResponse, str]:
    refresh_token, _ = issue_refresh_token(db, user)
    access_token = create_access_token(subject=user.user_id, role=user.role, account_id=user.account_id)
    return AuthResponse(user=user_response(user), access_token=access_token), refresh_token


def rotate_refresh_token(db: Session, raw_refresh_token: str) -> tuple[AuthResponse, str]:
    now = datetime.now(timezone.utc)
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh_token)))
    if not record or record.revoked_at or record.expires_at <= now:
        raise AuthenticationError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")
    user = db.get(User, record.user_id)
    if not user or user.status != "ACTIVE":
        raise AuthenticationError("Invalid refresh token", code="INVALID_REFRESH_TOKEN")

    new_raw, new_record = issue_refresh_token(db, user)
    record.revoked_at = now
    record.replaced_by = new_record.id
    access_token = create_access_token(subject=user.user_id, role=user.role, account_id=user.account_id)
    return AuthResponse(user=user_response(user), access_token=access_token), new_raw


def revoke_refresh_token(db: Session, raw_refresh_token: str | None) -> None:
    if not raw_refresh_token:
        return
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_refresh_token)))
    if record and not record.revoked_at:
        record.revoked_at = datetime.now(timezone.utc)
