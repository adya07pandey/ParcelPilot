from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthResponse, LoginRequest, UserResponse, user_response
from app.auth.service import authenticate_user, issue_auth_response, revoke_refresh_token, rotate_refresh_token
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.refresh_token_days * 24 * 60 * 60,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=get_settings().refresh_cookie_name, path="/api/v1/auth")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, payload.email, payload.password)
    auth_response, refresh_token = issue_auth_response(db, user)
    db.commit()
    set_refresh_cookie(response, refresh_token)
    return auth_response


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    raw_token = request.cookies.get(get_settings().refresh_cookie_name)
    if not raw_token:
        raise AuthenticationError("Missing refresh token", code="MISSING_REFRESH_TOKEN")
    auth_response, new_refresh_token = rotate_refresh_token(db, raw_token)
    db.commit()
    set_refresh_cookie(response, new_refresh_token)
    return auth_response


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    revoke_refresh_token(db, request.cookies.get(get_settings().refresh_cookie_name))
    db.commit()
    clear_refresh_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(current_user)
