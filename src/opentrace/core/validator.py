"""Source adapter validation engine with deterministic fixture and live test modes."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

from opentrace.api.schemas.common import SourceStatus
from opentrace.modules.base import OSINTModule
from opentrace.modules.registry import ModuleRegistry, get_default_registry


@dataclass
class ValidationResult:
    """The outcome of validating a single OSINT module."""

    module_id: str
    source_name: str
    target_type: str
    category: str
    mode: str  # 'fixture' or 'live'
    passed: bool
    status: str
    finding_count: int
    duration_ms: float
    message: str


# Deterministic standard test fixtures
FIXTURES: dict[str, str] = {
    "username": "octocat",
    "email": "developer@example.com",
    "phone": "+14155552671",
    "name": "Grace Hopper",
}


async def validate_module(module: OSINTModule, live: bool = False) -> ValidationResult:
    """Validate a single module against deterministic fixtures or live remote endpoints."""
    meta = module.metadata
    target_type = meta.supported_targets[0].value
    target_val = FIXTURES.get(target_type, "octocat")
    start_time = time.perf_counter()

    ctx = {
        "investigation_id": "val-test-0001",
        "target_type": target_type,
        "validation_mode": "live" if live else "fixture",
    }

    try:
        if not live:
            # Deterministic fixture mode:
            # Check module metadata integrity and dry execution
            assert meta.id, "Module metadata missing id"
            assert meta.name, "Module metadata missing name"
            assert meta.version, "Module metadata missing version"
            assert meta.source_name, "Module metadata missing source_name"
            assert meta.supported_targets, "Module metadata missing supported_targets"

            # Execute run against fixture target
            findings = await asyncio.wait_for(
                module.run(target_val, context=ctx), timeout=meta.timeout or 10.0
            )
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Validate finding structure
            assert isinstance(findings, list), "Module run() must return a list"
            for f in findings:
                assert "id" in f, "Finding missing id"
                assert "status" in f, "Finding missing status"
                assert "source_status" in f or f.get("status"), "Finding missing status tracking"

            st = findings[0].get("source_status", "succeeded") if findings else "no_match"
            return ValidationResult(
                module_id=meta.id,
                source_name=meta.source_name,
                target_type=target_type,
                category=meta.category,
                mode="fixture",
                passed=True,
                status=str(st),
                finding_count=len(findings),
                duration_ms=round(duration_ms, 2),
                message="Fixture executed successfully with compliant finding schemas",
            )
        else:
            # Live integration mode: execute against actual remote endpoints
            findings = await asyncio.wait_for(
                module.run(target_val, context=ctx), timeout=meta.timeout or 10.0
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            st = findings[0].get("source_status", "succeeded") if findings else "no_match"
            is_valid = st in (
                SourceStatus.succeeded.value,
                SourceStatus.no_match.value,
                SourceStatus.skipped.value,
                SourceStatus.rate_limited.value,
                SourceStatus.blocked.value,
                SourceStatus.unavailable.value,
            )

            return ValidationResult(
                module_id=meta.id,
                source_name=meta.source_name,
                target_type=target_type,
                category=meta.category,
                mode="live",
                passed=is_valid,
                status=str(st),
                finding_count=len(findings),
                duration_ms=round(duration_ms, 2),
                message=f"Live response: status={st}",
            )

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        return ValidationResult(
            module_id=meta.id,
            source_name=meta.source_name,
            target_type=target_type,
            category=meta.category,
            mode="live" if live else "fixture",
            passed=False,
            status=SourceStatus.error.value,
            finding_count=0,
            duration_ms=round(duration_ms, 2),
            message=f"{type(exc).__name__}: {str(exc)}",
        )


async def validate_all_modules(
    registry: ModuleRegistry | None = None,
    live: bool = False,
    target_type: str | None = None,
    category: str | None = None,
) -> list[ValidationResult]:
    """Validate all or filtered modules concurrently with bounded concurrency."""
    reg = registry or get_default_registry()
    modules = reg.list_all()

    if target_type:
        modules = [
            m for m in modules if any(t.value == target_type for t in m.metadata.supported_targets)
        ]

    if category:
        modules = [m for m in modules if m.metadata.category == category]

    semaphore = asyncio.Semaphore(5)

    async def _sem_val(m: OSINTModule) -> ValidationResult:
        async with semaphore:
            return await validate_module(m, live=live)

    return await asyncio.gather(*[_sem_val(m) for m in modules])
