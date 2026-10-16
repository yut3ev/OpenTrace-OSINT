"""JSON report exporter."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def _json_serial(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_json(investigation: dict[str, Any], indent: int = 2) -> str:
    """Export an investigation as formatted JSON."""
    return json.dumps(investigation, default=_json_serial, indent=indent, ensure_ascii=False)
