import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("invoicepilot")


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "app_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409, code="conflict")


class ApprovalBlockedError(AppError):
    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message, status_code=422, code="approval_blocked")
        self.issues = issues or []


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    payload: dict = {"detail": exc.message, "code": exc.code}
    if isinstance(exc, ApprovalBlockedError):
        payload["issues"] = exc.issues
    return JSONResponse(status_code=exc.status_code, content=payload)


async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})


async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        msg = error.get("msg", "Invalid value")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content={"detail": messages[0] if messages else "Invalid request", "issues": messages, "code": "validation_error"},
    )


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppError):
        return await app_error_handler(_request, exc)
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again.", "code": "internal_error"},
    )
