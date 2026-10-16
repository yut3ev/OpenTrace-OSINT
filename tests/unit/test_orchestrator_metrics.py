"""Unit tests for orchestrator honest metric counting and cancellation behavior."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from opentrace.api.schemas.common import FindingStatus, TargetType
from opentrace.api.schemas.investigation import InvestigationRequest, InvestigationStatus
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.modules.base import ModuleMetadata, OSINTModule
from opentrace.modules.registry import ModuleRegistry


class MockImmediateModule(OSINTModule):
    """Module that returns an immediate positive match."""

    metadata = ModuleMetadata(
        id="mock.fast",
        name="Fast Mock",
        version="1.0.0",
        source_name="Fast Mock Source",
        description="Fast mock test source",
        category="mock",
        supported_targets=[TargetType.username],
        source_url="https://mock.example.com/fast",
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [
            {
                "id": "mock-finding-1",
                "module_id": "mock.fast",
                "source_name": "Fast Mock Source",
                "target_type": "username",
                "status": FindingStatus.found.value,
                "title": "Fast finding",
                "evidence": "Found immediately",
                "observed_at": "2026-10-16T12:00:00Z",
                "confidence": "high",
                "data": {},
            }
        ]


class MockFailingModule(OSINTModule):
    """Module that returns an error status finding."""

    metadata = ModuleMetadata(
        id="mock.fail",
        name="Failing Mock",
        version="1.0.0",
        source_name="Failing Mock Source",
        description="Failing mock test source",
        category="mock",
        supported_targets=[TargetType.username],
        source_url="https://mock.example.com/fail",
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return [
            {
                "id": "mock-finding-fail",
                "module_id": "mock.fail",
                "source_name": "Failing Mock Source",
                "target_type": "username",
                "status": FindingStatus.error.value,
                "title": "Failed finding",
                "evidence": "Remote API 500 internal server error",
                "observed_at": "2026-10-16T12:00:00Z",
                "confidence": "none",
                "data": {},
            }
        ]


class MockHangingModule(OSINTModule):
    """Module that sleeps to simulate a long-running module for cancellation testing."""

    metadata = ModuleMetadata(
        id="mock.hanging",
        name="Hanging Mock",
        version="1.0.0",
        source_name="Hanging Mock Source",
        description="Hanging mock test source",
        category="mock",
        supported_targets=[TargetType.username],
        source_url="https://mock.example.com/hanging",
        timeout=10.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        await asyncio.sleep(5.0)
        return []


@pytest.mark.asyncio
async def test_error_finding_not_counted_as_no_match() -> None:
    """Error findings must increment metrics.error, not metrics.no_match."""
    registry = ModuleRegistry()
    registry.register(MockFailingModule())
    registry.register(MockImmediateModule())

    orchestrator = InvestigationOrchestrator(registry=registry)
    req = InvestigationRequest(
        username="testuser",
        modules=["mock.fail", "mock.fast"],
    )

    resp = await orchestrator.run_investigation(req)
    assert resp.status in (InvestigationStatus.partial, InvestigationStatus.completed)
    assert resp.summary.metrics.attempted == 2
    assert resp.summary.metrics.succeeded == 1
    assert resp.summary.metrics.error == 1
    assert resp.summary.metrics.no_match == 0  # CRUCIAL: never falsely counted as no_match!


@pytest.mark.asyncio
async def test_cancellation_preserves_partial_results() -> None:
    """When an investigation is cancelled midway, partial findings from completed modules are retained."""
    registry = ModuleRegistry()
    registry.register(MockImmediateModule())
    registry.register(MockHangingModule())

    orchestrator = InvestigationOrchestrator(registry=registry)
    req = InvestigationRequest(
        username="testuser",
        modules=["mock.fast", "mock.hanging"],
    )

    task = asyncio.create_task(orchestrator.run_investigation(req))
    # Give fast module enough time to complete
    await asyncio.sleep(0.3)
    task.cancel()

    resp = await task
    assert resp.status == InvestigationStatus.cancelled
    # The fast module completed before cancellation, so its finding must be preserved!
    assert len(resp.findings) >= 1
    found_titles = [
        getattr(f, "title", None) or (f.get("title") if isinstance(f, dict) else None)
        for f in resp.findings
    ]
    assert "Fast finding" in found_titles
    assert resp.summary.metrics.attempted >= 1
    assert resp.summary.metrics.succeeded >= 1
