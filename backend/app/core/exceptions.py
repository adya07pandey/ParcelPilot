from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code = 400
    code = "APP_ERROR"
    message = "Application error"

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        self.message = message or self.message
        self.code = code or self.code


class AuthenticationError(AppException):
    status_code = 401
    code = "AUTHENTICATION_REQUIRED"
    message = "Authentication required"


class AuthorizationError(AppException):
    status_code = 403
    code = "FORBIDDEN"
    message = "You are not allowed to access this resource"


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found"


class ValidationError(AppException):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Invalid request"


class ExternalServiceError(AppException):
    status_code = 502
    code = "EXTERNAL_SERVICE_ERROR"
    message = "External service error"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "request_id": request_id}},
    )
