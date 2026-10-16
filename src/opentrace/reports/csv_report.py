"""CSV report exporter with CSV injection protections."""

from __future__ import annotations

import csv
import io
from typing import Any

# Dangerous prefixes in spreadsheet software that trigger formula execution
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(value: Any) -> str:
    """Sanitize cell value to neutralize spreadsheet formula injection (CSV injection)."""
    if value is None:
        return ""
    text = str(value)
    if text.startswith(_FORMULA_PREFIXES):
        # Prefix with single quote to force spreadsheet programs to treat it as text
        return "'" + text
    return text


def export_csv(investigation: dict[str, Any]) -> str:
    """Export investigation findings as a CSV string."""
    findings = investigation.get("findings", [])
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    headers = [
        "finding_id",
        "module_id",
        "module_version",
        "target_type",
        "status",
        "title",
        "evidence",
        "source_name",
        "source_url",
        "observed_at",
        "confidence",
        "evidence_hash",
    ]
    writer.writerow(headers)

    for f in findings:
        row = [
            _sanitize_csv_cell(f.get("id", "")),
            _sanitize_csv_cell(f.get("module_id", "")),
            _sanitize_csv_cell(f.get("module_version", "")),
            _sanitize_csv_cell(f.get("target_type", "")),
            _sanitize_csv_cell(f.get("status", "")),
            _sanitize_csv_cell(f.get("title", "")),
            _sanitize_csv_cell(f.get("evidence", "")),
            _sanitize_csv_cell(f.get("source_name", "")),
            _sanitize_csv_cell(f.get("source_url", "")),
            _sanitize_csv_cell(f.get("observed_at", "")),
            _sanitize_csv_cell(f.get("confidence", "")),
            _sanitize_csv_cell(f.get("evidence_hash", "")),
        ]
        writer.writerow(row)

    return output.getvalue()
