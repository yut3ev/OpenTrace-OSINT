"""Source catalog and discovery endpoints querying manifest and active registry."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from opentrace.api.dependencies import get_registry
from opentrace.modules.manifest import get_source_manifest_entry, load_manifest
from opentrace.modules.registry import ModuleRegistry

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceResponse(BaseModel):
    """Manifest source descriptor augmented with runtime registration state."""

    id: str
    name: str
    category: str
    target_type: str
    access_type: str
    source_url: str
    status: str
    capabilities: list[str]
    description: str
    limitations: list[str]
    api_url: str | None = None
    is_active: bool = False


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
    status: Annotated[str | None, Query(description="Filter by manifest status")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    target_type: Annotated[str | None, Query(description="Filter by target type")] = None,
) -> list[SourceResponse]:
    """List all sources defined in the manifest, including active and planned."""
    manifest_sources = load_manifest()
    registered_ids = {m.metadata.id for m in registry.list_all()}

    results: list[SourceResponse] = []
    for s in manifest_sources:
        if status and s.status.lower() != status.lower():
            continue
        if category and s.category.lower() != category.lower():
            continue
        if target_type and s.target_type.lower() != target_type.lower():
            continue

        results.append(
            SourceResponse(
                id=s.id,
                name=s.name,
                category=s.category,
                target_type=s.target_type,
                access_type=s.access_type,
                source_url=s.source_url,
                status=s.status,
                capabilities=s.capabilities,
                description=s.description,
                limitations=s.limitations,
                api_url=s.api_url,
                is_active=s.id in registered_ids,
            )
        )
    return results


@router.get("/health/summary")
async def get_sources_health_summary(
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
) -> dict[str, Any]:
    """Retrieve operational health summary for all registered active sources."""
    all_mods = registry.list_all()
    health_results: list[dict[str, Any]] = []
    for mod in all_mods:
        health_results.append(await mod.health_check())

    return {
        "total_active_sources": len(all_mods),
        "healthy_count": sum(1 for h in health_results if h.get("status") == "healthy"),
        "free_count": sum(1 for h in health_results if h.get("is_free", True)),
        "requires_key_count": sum(1 for h in health_results if h.get("requires_api_key", False)),
        "sources": health_results,
    }


@router.get("/{source_id}/health")
async def get_source_health(
    source_id: str,
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
) -> dict[str, Any]:
    """Perform runtime health check for a specific source adapter."""
    mod = registry.get(source_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Active module '{source_id}' not found.")
    return await mod.health_check()


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
) -> SourceResponse:
    """Retrieve details for a specific source by ID."""
    entry = get_source_manifest_entry(source_id)
    if not entry:
        # Fall back to active registry
        mod = registry.get(source_id)
        if not mod:
            raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
        meta = mod.metadata
        return SourceResponse(
            id=meta.id,
            name=meta.name,
            category=getattr(meta, "category", "general"),
            target_type=meta.supported_targets[0].value if meta.supported_targets else "unknown",
            access_type=getattr(meta, "access_type", "public_web"),
            source_url=meta.source_url,
            status=meta.implementation_status,
            capabilities=["active_module"],
            description=meta.description,
            limitations=meta.limitations,
            is_active=True,
        )

    registered_ids = {m.metadata.id for m in registry.list_all()}
    return SourceResponse(
        id=entry.id,
        name=entry.name,
        category=entry.category,
        target_type=entry.target_type,
        access_type=entry.access_type,
        source_url=entry.source_url,
        status=entry.status,
        capabilities=entry.capabilities,
        description=entry.description,
        limitations=entry.limitations,
        api_url=entry.api_url,
        is_active=entry.id in registered_ids,
    )
