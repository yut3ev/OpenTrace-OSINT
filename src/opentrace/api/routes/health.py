"""Health check endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import opentrace
from opentrace.api.dependencies import get_app_settings
from opentrace.config import Settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Safe health response without leaking internal server paths or secrets."""

    status: str
    version: str
    storage_mode: str


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> HealthResponse:
    """Return application operational status and storage engine."""
    return HealthResponse(
        status="ok",
        version=opentrace.__version__,
        storage_mode=settings.storage_mode,
    )
