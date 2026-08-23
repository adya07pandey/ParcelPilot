import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from jose import JWTError, jwt

from app.core.config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$argon2"):
        try:
            return password_hasher.verify(stored_hash, password)
        except (VerifyMismatchError, VerificationError):
            return False

    # Legacy support for workbook/demo SHA-256 hashes.
    if len(stored_hash) == 64:
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return secrets.compare_digest(digest, stored_hash)

    return False


def create_access_token(*, subject: str, role: str, account_id: str | None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "account_id": account_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
