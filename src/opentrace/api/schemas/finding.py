"""Finding schema for API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from opentrace.api.schemas.common import Confidence, FindingStatus, TargetType


class FindingSchema(BaseModel):
    """A single finding produced by an OSINT module."""

    id: str = Field(..., description="Unique finding identifier")
    investigation_id: str = Field(..., description="Parent investigation ID")
    module_id: str = Field(..., description="Module that produced this finding")
    module_version: str = Field(default="0.1.0", description="Version of the producing module")
    target_type: TargetType = Field(..., description="Type of target investigated")
    status: FindingStatus = Field(..., description="Result status")
    title: str = Field(..., description="Human-readable title")
    evidence: str = Field(..., description="Evidence explanation for this finding")
    source_name: str = Field(..., description="Name of the source checked")
    source_url: str | None = Field(default=None, description="URL of the source")
    observed_at: datetime = Field(..., description="UTC timestamp of observation")
    confidence: Confidence = Field(default=Confidence.none, description="Confidence level")
    data: dict[str, Any] = Field(default_factory=dict, description="Structured evidence data")
    evidence_hash: str | None = Field(
        default=None,
        description="Integrity hash of the evidence, not proof of source truthfulness",
    )

    model_config = {"from_attributes": True}
