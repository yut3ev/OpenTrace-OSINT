"""Module discovery and capability inspection endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from opentrace.api.dependencies import get_registry
from opentrace.modules.registry import ModuleRegistry

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleInfoResponse(BaseModel):
    """Module capability and status descriptor."""

    id: str
    name: str
    version: str
    supported_targets: list[str]
    enabled: bool
    implementation_status: str
    source: str
    limitations: list[str]


@router.get("", response_model=list[ModuleInfoResponse])
async def list_modules(
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
) -> list[ModuleInfoResponse]:
    """List all registered OSINT modules and their implementation status."""
    result: list[ModuleInfoResponse] = []
    for mod in registry.list_all():
        meta = mod.metadata
        result.append(
            ModuleInfoResponse(
                id=meta.id,
                name=meta.name,
                version=meta.version,
                supported_targets=[t.value for t in meta.supported_targets],
                enabled=meta.enabled,
                implementation_status=meta.implementation_status,
                source=meta.source_name,
                limitations=meta.limitations,
            )
        )
    return result
