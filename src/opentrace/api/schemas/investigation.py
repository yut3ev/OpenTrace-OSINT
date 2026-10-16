"""Investigation request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from opentrace.api.schemas.common import Confidence, InvestigationStatus
from opentrace.api.schemas.finding import FindingSchema


class InvestigationRequest(BaseModel):
    """Request to start an investigation."""

    username: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    modules: list[str] | None = Field(default=None, description="Specific modules to run")
    max_runtime_seconds: float | None = Field(
        default=None, ge=1, le=120, description="Maximum runtime in seconds"
    )

    @model_validator(mode="after")
    def at_least_one_target(self) -> InvestigationRequest:
        """Ensure at least one target type is provided."""
        if not any([self.username, self.email, self.phone]):
            raise ValueError("At least one of username, email, or phone is required")
        return self


class EntitySchema(BaseModel):
    """A typed entity extracted from findings."""

    id: str
    type: str
    value: str
    display_label: str


class EdgeSchema(BaseModel):
    """An evidence-backed relationship between entities."""

    source_entity_id: str
    dest_entity_id: str
    relation: str
    basis: str
    confidence: Confidence
    evidence_ids: list[str] = Field(default_factory=list)
    label: str = Field(default="candidate", description="candidate or confirmed")


class SummarySchema(BaseModel):
    """Summary statistics for an investigation."""

    total: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    duration_seconds: float | None = None
    module_statuses: dict[str, str] = Field(default_factory=dict)


class InvestigationResponse(BaseModel):
    """Full investigation response."""

    id: str
    status: InvestigationStatus
    created_at: datetime
    completed_at: datetime | None = None
    request: dict[str, Any] = Field(default_factory=dict)
    findings: list[FindingSchema] = Field(default_factory=list)
    entities: list[EntitySchema] = Field(default_factory=list)
    edges: list[EdgeSchema] = Field(default_factory=list)
    summary: SummarySchema = Field(default_factory=SummarySchema)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}
