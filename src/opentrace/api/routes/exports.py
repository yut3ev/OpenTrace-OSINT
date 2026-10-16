"""Investigation report export endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from opentrace.api.dependencies import get_storage
from opentrace.core.errors import ExportError, InvestigationNotFoundError
from opentrace.reports.csv_report import export_csv
from opentrace.reports.html_report import export_html
from opentrace.reports.json_report import export_json
from opentrace.storage.interface import StorageBackend

router = APIRouter(prefix="/investigations", tags=["exports"])


@router.get("/{investigation_id}/export")
async def export_investigation(
    investigation_id: str,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    format: Annotated[str, Query(pattern="^(json|csv|html)$")] = "json",
) -> Response:
    """Export investigation findings as JSON, CSV, or HTML."""
    record = await storage.get_investigation(investigation_id)
    if not record:
        raise InvestigationNotFoundError(investigation_id)

    fmt = format.lower()
    if fmt == "json":
        content = export_json(record)
        media_type = "application/json"
        filename = f"opentrace-{investigation_id}.json"
    elif fmt == "csv":
        content = export_csv(record)
        media_type = "text/csv; charset=utf-8"
        filename = f"opentrace-{investigation_id}.csv"
    elif fmt == "html":
        content = export_html(record)
        media_type = "text/html; charset=utf-8"
        filename = f"opentrace-{investigation_id}.html"
    else:
        raise ExportError(f"Unsupported export format '{format}'")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
