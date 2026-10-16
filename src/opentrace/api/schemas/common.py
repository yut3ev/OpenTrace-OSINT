"""Common enumerations and base schemas shared across the API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class TargetType(StrEnum):
    """Types of investigation targets."""

    username = "username"
    email = "email"
    phone = "phone"
    name = "name"
    web = "web"


class FindingStatus(StrEnum):
    """Status of a single finding from a module."""

    found = "found"
    not_found = "not_found"
    unknown = "unknown"
    info = "info"
    error = "error"


class InvestigationStatus(StrEnum):
    """Lifecycle status of an investigation."""

    queued = "queued"
    running = "running"
    completed = "completed"
    partial = "partial"
    failed = "failed"
    cancelled = "cancelled"


class SourceStatus(StrEnum):
    """Granular execution status of a specific source adapter."""

    registered = "registered"
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    no_match = "no_match"
    rate_limited = "rate_limited"
    blocked = "blocked"
    unavailable = "unavailable"
    error = "error"
    skipped = "skipped"


class VerificationStatus(StrEnum):
    """Evidence verification status for a match."""

    verified = "verified"
    unverified = "unverified"
    ambiguous = "ambiguous"
    candidate = "candidate"


class Confidence(StrEnum):
    """Confidence level for a finding."""

    none = "none"
    low = "low"
    medium = "medium"
    high = "high"


class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard API error response."""

    error: ErrorDetail
