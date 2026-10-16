"""Finding deduplication without losing provenance."""

from __future__ import annotations

from typing import Any


def _dedup_key(finding: dict[str, Any]) -> str:
    """Generate a deduplication key for a finding."""
    return "|".join(
        [
            str(finding.get("module_id", "")),
            str(finding.get("target_type", "")),
            str(finding.get("status", "")),
            str(finding.get("source_url", "")),
        ]
    )


def deduplicate_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate findings by (module_id, target_type, status, source_url).

    Keeps the first occurrence. Merges evidence text from duplicates into
    the surviving finding. Never drops provenance information.
    """
    seen: dict[str, dict[str, Any]] = {}
    result: list[dict[str, Any]] = []

    for finding in findings:
        key = _dedup_key(finding)
        if key in seen:
            # Merge evidence from duplicate into the surviving finding
            existing = seen[key]
            dup_evidence = finding.get("evidence", "")
            if dup_evidence and dup_evidence not in existing.get("evidence", ""):
                existing["evidence"] = f"{existing.get('evidence', '')} | {dup_evidence}"
        else:
            seen[key] = finding
            result.append(finding)

    return result
