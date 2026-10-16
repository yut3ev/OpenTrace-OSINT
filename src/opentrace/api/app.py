"""FastAPI application factory and middleware configuration."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import opentrace
from opentrace.api.error_handlers import register_error_handlers
from opentrace.api.routes.exports import router as exports_router
from opentrace.api.routes.health import router as health_router
from opentrace.api.routes.investigations import router as investigations_router
from opentrace.api.routes.modules import router as modules_router
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

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(health_router)
    v1_router.include_router(modules_router)
    v1_router.include_router(investigations_router)
    v1_router.include_router(exports_router)

    app.include_router(v1_router)

    return app


app = create_app()
