from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    account_id: str | None = None
    company: str | None = None


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


def user_response(user) -> UserResponse:
    return UserResponse(
        id=user.user_id,
        name=user.name,
        email=user.email,
        role=str(user.role or "").upper(),
        account_id=user.account_id,
        company=user.company,
    )
