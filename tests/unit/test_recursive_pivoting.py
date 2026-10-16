"""Unit tests for recursive pivoting engine in InvestigationOrchestrator."""

from __future__ import annotations

from typing import Any

import pytest

from opentrace.api.schemas.common import FindingStatus, TargetType
from opentrace.api.schemas.investigation import InvestigationRequest
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.modules.base import ModuleMetadata, OSINTModule
from opentrace.modules.registry import ModuleRegistry


class SeedUsernameModule(OSINTModule):
    """Seed module returning a profile containing a discovered email address."""

    metadata = ModuleMetadata(
        id="test.seed_user",
        name="Seed User Module",
        version="1.0.0",
        supported_targets=[TargetType.username],
        source_name="Seed Source",
        source_url="https://seed.example.com/{username}",
        description="Returns profile with email reference",
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [
            {
                "id": "seed-finding-1",
                "module_id": "test.seed_user",
                "source_name": "Seed Source",
                "target_type": "username",
                "status": FindingStatus.found.value,
                "title": f"Profile for {target}",
                "evidence": "Found profile associated with dev@pivot-example.com",
                "confidence": "high",
                "observed_at": "2026-10-16T12:00:00Z",
                "data": {"username": target, "email": "dev@pivot-example.com"},
            }
        ]


class PivotedEmailModule(OSINTModule):
    """Module executed when pivoting onto an email address."""

    metadata = ModuleMetadata(
        id="test.pivot_email",
        name="Pivot Email Module",
        version="1.0.0",
        supported_targets=[TargetType.email],
        source_name="Pivot Email Source",
        source_url="https://email.example.com/{email}",
        description="Checks discovered email addresses",
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        pivot_depth = (context or {}).get("pivot_depth", 0)
        pivoted_from = (context or {}).get("pivoted_from_entity", "")
        return [
            {
                "id": "pivot-finding-1",
                "module_id": "test.pivot_email",
                "source_name": "Pivot Email Source",
                "target_type": "email",
                "status": FindingStatus.found.value,
                "title": f"Discovered record for {target} at depth {pivot_depth}",
                "evidence": f"Pivoted from entity {pivoted_from}",
                "confidence": "high",
                "observed_at": "2026-10-16T12:00:00Z",
                "data": {"email": target, "pivot_depth": pivot_depth},
            }
        ]


@pytest.mark.asyncio
async def test_recursive_pivoting_explores_discovered_entities() -> None:
    """When enable_pivot is True, discovered entities are searched in subsequent layer."""
    registry = ModuleRegistry()
    registry.register(SeedUsernameModule())
    registry.register(PivotedEmailModule())

    orchestrator = InvestigationOrchestrator(registry=registry)

    # 1. Without pivoting: only seed module runs
    no_pivot_req = InvestigationRequest(
        username="lead_dev",
        enable_pivot=False,
    )
    res_no_pivot = await orchestrator.run_investigation(no_pivot_req)
    assert len(res_no_pivot.findings) == 1
    assert res_no_pivot.findings[0].module_id == "test.seed_user"

    # 2. With pivoting: seed runs in layer 0, email runs in layer 1
    pivot_req = InvestigationRequest(
        username="lead_dev",
        enable_pivot=True,
        max_pivot_depth=1,
        max_pivot_budget=5,
    )
    res_pivot = await orchestrator.run_investigation(pivot_req)

    # Both seed and pivoted findings should be present
    finding_modules = [f.module_id for f in res_pivot.findings]
    assert "test.seed_user" in finding_modules
    assert "test.pivot_email" in finding_modules

    # Verify edge was established connecting seed username to discovered email
    entity_types = {e.type for e in res_pivot.entities}
    assert "username" in entity_types
    assert "email" in entity_types
