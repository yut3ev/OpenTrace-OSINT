"""Finding schema for API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from opentrace.api.schemas.common import (
    Confidence,
    FindingStatus,
    SourceStatus,
    TargetType,
    VerificationStatus,
)


class FindingSchema(BaseModel):
    """A single finding produced by an OSINT source adapter."""

    id: str = Field(..., description="Unique finding identifier")
    investigation_id: str = Field(..., description="Parent investigation ID")
    module_id: str = Field(..., description="Module identifier")
    module_version: str = Field(default="0.1.0", description="Version of the producing module")
    source_id: str | None = Field(default=None, description="Granular source platform identifier")
    source_name: str = Field(..., description="Name of the source checked")
    source_url: str | None = Field(default=None, description="URL of the source platform or check")
    target_type: TargetType = Field(..., description="Type of target investigated")
    search_type: TargetType | str | None = Field(
        default=None, description="Explicit search mode for the query"
    )
    matched_identifier: str | None = Field(
        default=None, description="The normalized query identifier matched"
    )
    display_name: str | None = Field(
        default=None, description="Public profile or entity display name"
    )
    username: str | None = Field(default=None, description="Observed handle or username")
    profile_url: str | None = Field(
        default=None, description="Direct URL to public profile if resolved"
    )
    public_evidence_url: str | None = Field(
        default=None, description="URL providing public evidence of the finding"
    )
    status: FindingStatus = Field(..., description="Finding outcome status")
    source_status: SourceStatus | str | None = Field(
        default=None, description="Granular source execution lifecycle status"
    )
    verification_status: VerificationStatus | str = Field(
        default=VerificationStatus.candidate,
        description="Verification state (verified, unverified, ambiguous, candidate)",
    )
    title: str = Field(..., description="Human-readable title")
    evidence: str = Field(..., description="Evidence explanation for this finding")
    observed_at: datetime = Field(..., description="UTC timestamp of observation")
    confidence: Confidence = Field(default=Confidence.none, description="Confidence level")
    confidence_reasons: list[str] = Field(
        default_factory=list, description="Explicit reasoning behind confidence level"
    )
    limitations: list[str] = Field(
        default_factory=list, description="Known source or accuracy limitations"
    )
    data: dict[str, Any] = Field(default_factory=dict, description="Structured evidence payload")
    evidence_hash: str | None = Field(
        default=None,
        description="Integrity hash of the evidence, not proof of source truthfulness",
    )

    model_config = {"from_attributes": True}
