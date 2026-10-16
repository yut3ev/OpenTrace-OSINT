"""Common enumerations and base schemas shared across the API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class TargetType(StrEnum):
    """Types of investigation targets."""

    username = "username"
    email = "email"
    phone = "phone"


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
