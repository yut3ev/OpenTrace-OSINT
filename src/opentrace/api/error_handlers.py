"""Centralized exception and error handling for the REST API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from opentrace.api.schemas.common import ErrorDetail, ErrorResponse
from opentrace.core.errors import (
    InvestigationNotFoundError,
    OpenTraceError,
    ValidationError,
)

logger = logging.getLogger("opentrace.api.errors")


def register_error_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application."""

    @app.exception_handler(InvestigationNotFoundError)
    async def not_found_handler(request: Request, exc: InvestigationNotFoundError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(code="NOT_FOUND", message=str(exc), request_id=req_id)
            ).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(code="VALIDATION_ERROR", message=str(exc), request_id=req_id)
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        message = "; ".join(
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors
        )
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(code="VALIDATION_ERROR", message=message, request_id=req_id)
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        code = "NOT_FOUND" if exc.status_code == 404 else f"HTTP_{exc.status_code}"
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(code=code, message=str(exc.detail), request_id=req_id)
            ).model_dump(),
        )

    @app.exception_handler(OpenTraceError)
    async def opentrace_error_handler(request: Request, exc: OpenTraceError) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.error("OpenTrace error: %s", exc)
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(code="OPENTRACE_ERROR", message=str(exc), request_id=req_id)
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled server exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected internal server error occurred.",
                    request_id=req_id,
                )
            ).model_dump(),
        )
