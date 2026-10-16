"""Investigation endpoints including creation, listing, retrieval, deletion, SSE events, and retry."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from opentrace.api.dependencies import (
    get_event_bus,
    get_optional_user,
    get_orchestrator,
    get_storage,
)
from opentrace.api.schemas.investigation import InvestigationRequest, InvestigationResponse
from opentrace.core.errors import InvestigationNotFoundError
from opentrace.core.events import Event, EventBus
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.storage.interface import StorageBackend

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationResponse, status_code=200)
@router.post("/search", response_model=InvestigationResponse, status_code=200)
async def create_investigation(
    request: InvestigationRequest,
    orchestrator: Annotated[InvestigationOrchestrator, Depends(get_orchestrator)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> InvestigationResponse:
    """Run an investigation or unified search across selected compatible modules."""
    user_id = user["id"] if user else None
    return await orchestrator.run_investigation(request, user_id=user_id)


@router.get("", response_model=list[InvestigationResponse])
async def list_investigations(
    storage: Annotated[StorageBackend, Depends(get_storage)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> list[dict]:  # type: ignore[type-arg]
    """List recent investigations, scoped to current user if authenticated."""
    user_id = user["id"] if user else None
    return await storage.list_investigations(limit=limit, user_id=user_id)


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> dict:  # type: ignore[type-arg]
    """Retrieve an investigation by UUID, isolated by user ownership."""
    user_id = user["id"] if user else None
    record = await storage.get_investigation(investigation_id, user_id=user_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)
    return record


@router.delete("/{investigation_id}")
async def delete_investigation(
    investigation_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> dict[str, bool]:
    """Delete an investigation record with ownership verification."""
    user_id = user["id"] if user else None
    deleted = await storage.delete_investigation(investigation_id, user_id=user_id)
    if not deleted:
        raise InvestigationNotFoundError(investigation_id)
    return {"deleted": True}


@router.post("/{investigation_id}/retry", response_model=InvestigationResponse)
async def retry_investigation(
    investigation_id: str,
    orchestrator: Annotated[InvestigationOrchestrator, Depends(get_orchestrator)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> InvestigationResponse:
    """Retry failed, rate-limited, or unavailable sources for an investigation."""
    user_id = user["id"] if user else None
    return await orchestrator.retry_investigation(investigation_id, user_id=user_id)


@router.get("/{investigation_id}/events")
async def stream_events(
    investigation_id: str,
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> StreamingResponse:
    """Stream real-time investigation events via Server-Sent Events (SSE)."""
    user_id = user["id"] if user else None
    record = await storage.get_investigation(investigation_id, user_id=user_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)

    queue: asyncio.Queue[Event | None] = asyncio.Queue()

    async def event_handler(event: Event) -> None:
        event_inv_id = str(event.data.get("investigation_id", ""))
        if event_inv_id == investigation_id:
            await queue.put(event)
            if event.type.value in ("investigation.completed", "investigation.cancelled"):
                await queue.put(None)  # Signal end of stream

    await event_bus.subscribe(event_handler)

    from collections.abc import AsyncGenerator

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # If investigation is already completed or failed, emit current state and exit
            status = str(record.get("status", ""))
            if status in ("completed", "partial", "failed", "cancelled"):
                init_data = json.dumps({"status": status, "investigation_id": investigation_id})
                yield f"event: investigation.completed\ndata: {init_data}\n\n"
                return

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    if event is None:
                        break
                    payload = json.dumps(
                        {
                            "type": event.type.value,
                            "timestamp": event.timestamp.isoformat(),
                            "data": event.data,
                        }
                    )
                    yield f"event: {event.type.value}\ndata: {payload}\n\n"
                except TimeoutError:
                    # Heartbeat comment to keep SSE connection alive
                    yield ": ping\n\n"
        finally:
            await event_bus.unsubscribe(event_handler)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{investigation_id}/cancel")
async def cancel_investigation(
    investigation_id: str,
    orchestrator: Annotated[InvestigationOrchestrator, Depends(get_orchestrator)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> dict[str, Any]:
    """Cancel a running or queued investigation."""
    user_id = user["id"] if user else None
    record = await storage.get_investigation(investigation_id, user_id=user_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)
    cancelled = await orchestrator.cancel_investigation(investigation_id)
    return {"investigation_id": investigation_id, "cancelled": cancelled}


@router.get("/{investigation_id}/findings")
async def get_investigation_findings(
    investigation_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    status: str | None = None,
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> list[dict[str, Any]]:
    """Retrieve findings for an investigation with optional status filter."""
    user_id = user["id"] if user else None
    record = await storage.get_investigation(investigation_id, user_id=user_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)
    findings = list(record.get("findings", []))
    if status:
        findings = [
            f for f in findings if f.get("status") == status or f.get("source_status") == status
        ]
    return findings


@router.get("/{investigation_id}/sources")
async def get_investigation_sources(
    investigation_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    user: Annotated[dict[str, Any] | None, Depends(get_optional_user)] = None,
) -> dict[str, Any]:
    """Retrieve source execution breakdown and metrics for an investigation."""
    user_id = user["id"] if user else None
    record = await storage.get_investigation(investigation_id, user_id=user_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)
    summary = record.get("summary", {})
    return {
        "investigation_id": investigation_id,
        "module_statuses": summary.get("module_statuses", {}),
        "metrics": summary.get("metrics", {}),
    }
