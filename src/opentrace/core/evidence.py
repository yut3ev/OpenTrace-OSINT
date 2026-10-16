"""Evidence provenance records and integrity hashing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime


def compute_evidence_hash(
    source_url: str, status_code: int | None, summary: str | None = None
) -> str:
    """Compute a SHA-256 hash of evidence parameters for integrity checking.

    This hash is for deduplication and integrity, NOT proof that the source is truthful.
    """
    payload = f"{source_url}|{status_code}|{summary or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable record of evidence provenance."""

    module_id: str
    source_name: str
    source_url: str
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    raw_status_code: int | None = None
    response_summary: str = ""
    evidence_hash: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_hash:
            computed = compute_evidence_hash(
                self.source_url,
                self.raw_status_code,
                self.response_summary,
            )
            # frozen=True requires object.__setattr__
            object.__setattr__(self, "evidence_hash", computed)
