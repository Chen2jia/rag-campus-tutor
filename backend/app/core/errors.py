from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings


logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = get_request_id(request)
    log_level = logging.WARNING if exc.status_code >= 500 else logging.INFO
    logger.log(
        log_level,
        "handled_http_error request_id=%s status=%s path=%s detail=%s",
        request_id,
        exc.status_code,
        request.url.path,
        exc.detail,
    )
    return error_response(
        status_code=exc.status_code,
        code=http_error_code(exc.status_code),
        detail=exc.detail,
        request_id=request_id,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = get_request_id(request)
    logger.info(
        "validation_error request_id=%s path=%s errors=%s",
        request_id,
        request.url.path,
        exc.errors(),
    )
    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="validation_error",
        detail="Request validation failed",
        request_id=request_id,
        extra={"errors": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    logger.exception(
        "unhandled_error request_id=%s path=%s",
        request_id,
        request.url.path,
    )
    extra: dict[str, Any] = {}
    if settings.app_env != "production":
        extra["debug"] = exc.__class__.__name__
    return error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="internal_error",
        detail="Internal server error",
        request_id=request_id,
        extra=extra,
    )


def error_response(
    status_code: int,
    code: str,
    detail: Any,
    request_id: str,
    headers: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "detail": detail,
        "error": {
            "code": code,
            "request_id": request_id,
        },
    }
    if extra:
        body["error"].update(extra)
    response_headers = {"X-Request-ID": request_id}
    if headers:
        response_headers.update(headers)
    return JSONResponse(status_code=status_code, content=body, headers=response_headers)


def get_request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def http_error_code(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not_found"
    if status_code == status.HTTP_409_CONFLICT:
        return "conflict"
    if status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
        return "payload_too_large"
    if status_code >= 500:
        return "server_error"
    return "request_error"
