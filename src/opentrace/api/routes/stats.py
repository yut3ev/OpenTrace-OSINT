"""Platform investigation statistics and source coverage telemetry."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from opentrace.api.dependencies import get_registry, get_storage
from opentrace.modules.manifest import load_manifest
from opentrace.modules.registry import ModuleRegistry
from opentrace.storage.interface import StorageBackend

router = APIRouter(prefix="/stats", tags=["stats"])


class PlatformStatsResponse(BaseModel):
    """Aggregate statistics for investigations and source coverage."""

    total_investigations: int
    total_findings: int
    total_manifest_sources: int
    total_active_modules: int
    sources_by_status: dict[str, int]
    sources_by_category: dict[str, int]
    sources_by_target: dict[str, int]


@router.get("", response_model=PlatformStatsResponse)
async def get_platform_stats(
    storage: Annotated[StorageBackend, Depends(get_storage)],
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
) -> PlatformStatsResponse:
    """Return high-level statistics across all investigations and source catalog."""
    investigations = await storage.list_investigations(limit=1000)
    total_findings = sum(len(inv.get("findings", [])) for inv in investigations)

    manifest_sources = load_manifest()
    sources_by_status: dict[str, int] = {}
    sources_by_category: dict[str, int] = {}
    sources_by_target: dict[str, int] = {}

    for s in manifest_sources:
        sources_by_status[s.status] = sources_by_status.get(s.status, 0) + 1
        sources_by_category[s.category] = sources_by_category.get(s.category, 0) + 1
        sources_by_target[s.target_type] = sources_by_target.get(s.target_type, 0) + 1

    active_modules = len(registry.list_all())

    return PlatformStatsResponse(
        total_investigations=len(investigations),
        total_findings=total_findings,
        total_manifest_sources=len(manifest_sources),
        total_active_modules=active_modules,
        sources_by_status=sources_by_status,
        sources_by_category=sources_by_category,
        sources_by_target=sources_by_target,
    )
