"""FastAPI application factory and middleware configuration."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import opentrace
from opentrace.api.error_handlers import register_error_handlers
from opentrace.api.routes.exports import router as exports_router
from opentrace.api.routes.health import router as health_router
from opentrace.api.routes.investigations import router as investigations_router
from opentrace.api.routes.modules import router as modules_router
from opentrace.api.routes.sources import router as sources_router
from opentrace.api.routes.stats import router as stats_router
from opentrace.config import get_settings
from opentrace.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    settings = get_settings()
    setup_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="OpenTrace OSINT API",
        description="Evidence-first public digital-footprint investigation platform.",
        version=opentrace.__version__,
        lifespan=lifespan,
    )

    settings = get_settings()

    # CORS configuration
    has_wildcard = "*" in settings.cors_origins
    valid_origins = [o for o in settings.cors_origins if o != "*"]
    allow_origins = (
        ["*"]
        if (has_wildcard and not valid_origins)
        else (valid_origins or ["http://localhost:5173"])
    )
    allow_credentials = not has_wildcard

    cors_kwargs: dict[str, Any] = {
        "allow_origins": allow_origins,
        "allow_credentials": allow_credentials,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "Accept"],
    }
    if settings.cors_origin_regex:
        cors_kwargs["allow_origin_regex"] = settings.cors_origin_regex

    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # API key authentication middleware
    @app.middleware("http")
    async def api_key_auth_middleware(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        if request.method == "OPTIONS":
            res_opt: Response = await call_next(request)
            return res_opt

        path = request.url.path
        public_paths = {"/health", "/api/v1/health", "/docs", "/redoc", "/openapi.json"}
        if (
            path in public_paths
            or path.startswith("/docs")
            or path.startswith("/redoc")
            or path.startswith("/api/v1/auth")
        ):
            res_pub: Response = await call_next(request)
            return res_pub

        current_settings = get_settings()
        if current_settings.api_key:
            auth_header = request.headers.get("Authorization")
            api_key_header = request.headers.get("X-API-Key")

            provided_key = api_key_header
            if not provided_key and auth_header and auth_header.startswith("Bearer "):
                provided_key = auth_header[7:].strip()

            if not provided_key or provided_key != current_settings.api_key:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized: invalid or missing API key"},
                )

        res_next: Response = await call_next(request)
        return res_next

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

    # Centralized error handlers
    register_error_handlers(app)

    # Health check at root and /api/v1
    app.include_router(health_router)

    # API v1 Router
    from fastapi import APIRouter

    from opentrace.api.routes.auth import router as auth_router

    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(health_router)
    v1_router.include_router(auth_router)
    v1_router.include_router(modules_router)
    v1_router.include_router(sources_router)
    v1_router.include_router(stats_router)
    v1_router.include_router(investigations_router)
    v1_router.include_router(exports_router)

    app.include_router(v1_router)

    return app


app = create_app()
