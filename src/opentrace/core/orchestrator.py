"""Investigation orchestrator coordinating input normalization, execution, and correlation."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from opentrace.api.schemas.common import InvestigationStatus, TargetType
from opentrace.api.schemas.investigation import (
    EdgeSchema,
    EntitySchema,
    InvestigationRequest,
    InvestigationResponse,
    SummarySchema,
)
from opentrace.config import Settings, get_settings
from opentrace.core.correlation import build_edges, extract_entities
from opentrace.core.deduplication import deduplicate_findings
from opentrace.core.errors import ValidationError
from opentrace.core.events import Event, EventBus, EventType
from opentrace.core.normalization import normalize_email, normalize_phone, normalize_username
from opentrace.core.scheduler import BoundedScheduler
from opentrace.modules.base import OSINTModule
from opentrace.modules.registry import ModuleRegistry, get_default_registry
from opentrace.storage.interface import StorageBackend
from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage

logger = logging.getLogger("opentrace.core.orchestrator")


class InvestigationOrchestrator:
    """Coordinates the lifecycle of an OSINT investigation."""

    def __init__(
        self,
        storage: StorageBackend | None = None,
        registry: ModuleRegistry | None = None,
        event_bus: EventBus | None = None,
        scheduler: BoundedScheduler | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.event_bus = event_bus or EventBus()
        self.registry = registry or get_default_registry()

        if storage is not None:
            self.storage = storage
        elif self.settings.storage_mode == "sqlite":
            self.storage = SQLiteStorage(self.settings.sqlite_path)
        else:
            self.storage = MemoryStorage()

        self.scheduler = scheduler or BoundedScheduler(
            global_concurrency=self.settings.max_concurrency,
            per_host_concurrency=self.settings.per_host_concurrency,
            event_bus=self.event_bus,
        )

    def _normalize_targets(
        self, req: InvestigationRequest
    ) -> tuple[dict[TargetType, str], list[str]]:
        """Validate and normalize user-supplied targets. Returns (normalized_map, warnings)."""
        normalized: dict[TargetType, str] = {}
        warnings: list[str] = []

        if req.username:
            try:
                normalized[TargetType.username] = normalize_username(req.username)
            except ValidationError as e:
                warnings.append(f"Invalid username '{req.username}': {e}")

        if req.email:
            try:
                normalized[TargetType.email] = normalize_email(req.email)
            except ValidationError as e:
                warnings.append(f"Invalid email '{req.email}': {e}")

        if req.phone:
            try:
                normalized[TargetType.phone] = normalize_phone(req.phone)
            except ValidationError as e:
                warnings.append(f"Invalid phone '{req.phone}': {e}")

        return normalized, warnings

    def _select_modules(
        self,
        requested_modules: list[str] | None,
        active_target_types: list[TargetType],
    ) -> tuple[list[tuple[OSINTModule, TargetType]], list[str]]:
        """Select modules compatible with active targets. Returns (module_list, warnings)."""
        selected: list[tuple[OSINTModule, TargetType]] = []
        warnings: list[str] = []

        all_modules = self.registry.list_all()
        id_to_mod = {m.metadata.id: m for m in all_modules}

        if requested_modules:
            for mod_id in requested_modules:
                mod = id_to_mod.get(mod_id)
                if not mod:
                    warnings.append(f"Requested module '{mod_id}' was not found in registry.")
                    continue
                if not mod.metadata.enabled:
                    warnings.append(f"Module '{mod_id}' is currently disabled.")
                    continue

                # Match against supported active targets
                matched = False
                for target_type in active_target_types:
                    if mod.supports(target_type):
                        selected.append((mod, target_type))
                        matched = True
                if not matched:
                    warnings.append(
                        f"Module '{mod_id}' does not support any of the provided active targets."
                    )
        else:
            # Automatic selection: select all enabled modules for each active target type
            for target_type in active_target_types:
                mods_for_type = self.registry.list_for_target(target_type)
                for mod in mods_for_type:
                    selected.append((mod, target_type))

        return selected, warnings

    async def run_investigation(
        self, request: InvestigationRequest | dict[str, Any]
    ) -> InvestigationResponse:
        """Run a complete investigation end-to-end."""
        if isinstance(request, dict):
            req = InvestigationRequest(**request)
        else:
            req = request

        inv_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)
        start_time = time.perf_counter()

        normalized_targets, target_warnings = self._normalize_targets(req)
        warnings: list[str] = list(target_warnings)

        if not normalized_targets:
            # None of the targets were valid
            failed_resp = InvestigationResponse(
                id=inv_id,
                status=InvestigationStatus.failed,
                created_at=created_at,
                completed_at=datetime.now(UTC),
                request=req.model_dump(exclude_none=True),
                findings=[],
                entities=[],
                edges=[],
                summary=SummarySchema(total=0, by_status={}, duration_seconds=0.0),
                warnings=warnings or ["No valid targets provided."],
            )
            await self.storage.save_investigation(failed_resp.model_dump())
            return failed_resp

        # Select modules
        module_pairs, selection_warnings = self._select_modules(
            req.modules, list(normalized_targets.keys())
        )
        warnings.extend(selection_warnings)

        # Build initial investigation record
        initial_record = {
            "id": inv_id,
            "status": InvestigationStatus.running.value,
            "created_at": created_at.isoformat(),
            "request": req.model_dump(exclude_none=True),
            "findings": [],
            "entities": [],
            "edges": [],
            "summary": {"total": 0, "by_status": {}},
            "warnings": warnings,
        }
        await self.storage.save_investigation(initial_record)

        await self.event_bus.publish(
            Event(
                type=EventType.investigation_started,
                data={"investigation_id": inv_id, "targets": [t.value for t in normalized_targets]},
            )
        )

        if not module_pairs:
            warnings.append("No active modules matched the provided targets.")
            duration = round(time.perf_counter() - start_time, 3)
            resp = InvestigationResponse(
                id=inv_id,
                status=InvestigationStatus.completed,
                created_at=created_at,
                completed_at=datetime.now(UTC),
                request=req.model_dump(exclude_none=True),
                findings=[],
                entities=[],
                edges=[],
                summary=SummarySchema(total=0, by_status={}, duration_seconds=duration),
                warnings=warnings,
            )
            await self.storage.save_investigation(resp.model_dump())
            await self.event_bus.publish(
                Event(
                    type=EventType.investigation_completed,
                    data={"investigation_id": inv_id, "status": resp.status.value},
                )
            )
            return resp

        # Build scheduler tasks
        tasks = []
        for mod, target_type in module_pairs:
            target_val = normalized_targets[target_type]
            ctx = {
                "investigation_id": inv_id,
                "target_type": target_type.value,
                "observed_at": created_at.isoformat(),
            }
            tasks.append((mod, target_val, ctx))

        # Determine runtime limit
        max_runtime = min(
            req.max_runtime_seconds or self.settings.max_runtime,
            self.settings.max_runtime,
        )

        try:
            results = await asyncio.wait_for(
                self.scheduler.execute_tasks(tasks),
                timeout=max_runtime,
            )
        except TimeoutError:
            warnings.append(f"Investigation hit global runtime limit of {max_runtime}s.")
            results = []

        all_findings: list[dict[str, Any]] = []
        module_statuses: dict[str, str] = {}

        for mod_id, findings, status_str in results:
            module_statuses[mod_id] = status_str
            for f in findings:
                if "investigation_id" not in f or not f["investigation_id"]:
                    f["investigation_id"] = inv_id
                all_findings.append(f)

        # Deduplicate findings
        deduped = deduplicate_findings(all_findings)

        # Extract entities and edges
        raw_entities = extract_entities(deduped)
        raw_edges = build_edges(raw_entities, deduped)

        entities_schemas = [
            EntitySchema(id=e.id, type=e.type, value=e.value, display_label=e.display_label)
            for e in raw_entities
        ]
        edges_schemas = [
            EdgeSchema(
                source_entity_id=ed.source_entity_id,
                dest_entity_id=ed.dest_entity_id,
                relation=ed.relation,
                basis=ed.basis,
                confidence=ed.confidence,  # type: ignore[arg-type]
                evidence_ids=ed.evidence_ids,
                label=ed.label,
            )
            for ed in raw_edges
        ]

        # Calculate counts
        by_status: dict[str, int] = {}
        for f in deduped:
            st = str(f.get("status", "unknown"))
            by_status[st] = by_status.get(st, 0) + 1

        duration = round(time.perf_counter() - start_time, 3)

        # Determine overall investigation status
        if not module_statuses:
            final_status = (
                InvestigationStatus.completed if not results else InvestigationStatus.failed
            )
        elif all(s == "completed" for s in module_statuses.values()):
            final_status = InvestigationStatus.completed
        elif any(s == "completed" for s in module_statuses.values()):
            final_status = InvestigationStatus.partial
        else:
            final_status = InvestigationStatus.failed

        completed_at = datetime.now(UTC)
        summary = SummarySchema(
            total=len(deduped),
            by_status=by_status,
            duration_seconds=duration,
            module_statuses=module_statuses,
        )

        response = InvestigationResponse(
            id=inv_id,
            status=final_status,
            created_at=created_at,
            completed_at=completed_at,
            request=req.model_dump(exclude_none=True),
            findings=deduped,  # type: ignore[arg-type]
            entities=entities_schemas,
            edges=edges_schemas,
            summary=summary,
            warnings=warnings,
        )

        # Persist final result
        await self.storage.save_investigation(response.model_dump())

        await self.event_bus.publish(
            Event(
                type=EventType.investigation_completed,
                data={
                    "investigation_id": inv_id,
                    "status": final_status.value,
                    "findings_count": len(deduped),
                },
            )
        )

        return response
