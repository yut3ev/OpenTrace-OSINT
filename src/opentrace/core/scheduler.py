"""Bounded concurrency scheduler with per-host and global limits."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

from opentrace.api.schemas.common import FindingStatus
from opentrace.core.events import Event, EventBus, EventType
from opentrace.modules.base import OSINTModule

logger = logging.getLogger("opentrace.core.scheduler")


class BoundedScheduler:
    """Schedules and executes OSINT modules with bounded global and per-host concurrency."""

    def __init__(
        self,
        global_concurrency: int = 5,
        per_host_concurrency: int = 2,
        event_bus: EventBus | None = None,
    ) -> None:
        self.global_semaphore = asyncio.Semaphore(max(1, global_concurrency))
        self.per_host_limit = max(1, per_host_concurrency)
        self.host_semaphores: dict[str, asyncio.Semaphore] = {}
        self._host_lock = asyncio.Lock()
        self.event_bus = event_bus

    async def _get_host_semaphore(self, url: str) -> asyncio.Semaphore:
        """Retrieve or create a semaphore for the target host."""
        try:
            parsed = urlparse(url)
            host = parsed.netloc or "default"
        except Exception:
            host = "default"

        async with self._host_lock:
            if host not in self.host_semaphores:
                self.host_semaphores[host] = asyncio.Semaphore(self.per_host_limit)
            return self.host_semaphores[host]

    async def run_single_module(
        self,
        module: OSINTModule,
        target: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]], str]:
        """Execute a single module with concurrency bounds and timeouts.

        Returns (module_id, findings_list, status_string: 'completed' | 'failed' | 'timeout')
        """
        mod_id = module.metadata.id
        ctx = context or {}
        inv_id = ctx.get("investigation_id", "")
        host_sem = await self._get_host_semaphore(module.metadata.source_url)

        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    type=EventType.module_started,
                    data={
                        "investigation_id": inv_id,
                        "module_id": mod_id,
                        "target": target,
                    },
                )
            )

        timeout = module.metadata.timeout or 10.0

        try:
            async with self.global_semaphore:
                async with host_sem:
                    findings = await asyncio.wait_for(
                        module.run(target, context=ctx),
                        timeout=timeout,
                    )

            if self.event_bus:
                for f in findings:
                    await self.event_bus.publish(
                        Event(
                            type=EventType.finding_created,
                            data={"investigation_id": inv_id, "finding": f},
                        )
                    )
                await self.event_bus.publish(
                    Event(
                        type=EventType.module_completed,
                        data={
                            "investigation_id": inv_id,
                            "module_id": mod_id,
                            "findings_count": len(findings),
                        },
                    )
                )

            return mod_id, findings, "completed"

        except TimeoutError:
            logger.warning("Module '%s' timed out after %.1fs", mod_id, timeout)
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        type=EventType.module_failed,
                        data={
                            "investigation_id": inv_id,
                            "module_id": mod_id,
                            "reason": "timeout",
                        },
                    )
                )
            # Create a conservative finding documenting the timeout
            timeout_finding = {
                "id": f"{inv_id}-{mod_id}-timeout",
                "investigation_id": inv_id,
                "module_id": mod_id,
                "module_version": module.metadata.version,
                "target_type": module.metadata.supported_targets[0].value,
                "status": FindingStatus.unknown.value,
                "title": f"Module {mod_id} timed out",
                "evidence": f"Request exceeded module timeout of {timeout}s.",
                "source_name": module.metadata.source_name,
                "source_url": module.metadata.source_url,
                "observed_at": ctx.get("observed_at"),
                "confidence": "none",
                "data": {"error": "timeout"},
            }
            return mod_id, [timeout_finding], "timeout"

        except Exception as exc:
            logger.exception("Module '%s' failed with error: %s", mod_id, exc)
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        type=EventType.module_failed,
                        data={
                            "investigation_id": inv_id,
                            "module_id": mod_id,
                            "reason": str(exc),
                        },
                    )
                )
            error_finding = {
                "id": f"{inv_id}-{mod_id}-error",
                "investigation_id": inv_id,
                "module_id": mod_id,
                "module_version": module.metadata.version,
                "target_type": module.metadata.supported_targets[0].value,
                "status": FindingStatus.error.value,
                "title": f"Module {mod_id} execution failed",
                "evidence": f"Internal execution error: {type(exc).__name__}: {str(exc)}",
                "source_name": module.metadata.source_name,
                "source_url": module.metadata.source_url,
                "observed_at": ctx.get("observed_at"),
                "confidence": "none",
                "data": {"error": str(exc)},
            }
            return mod_id, [error_finding], "error"

    async def execute_tasks(
        self,
        tasks: list[tuple[OSINTModule, str, dict[str, Any]]],
        on_result: Any = None,
    ) -> list[tuple[str, list[dict[str, Any]], str]]:
        """Run multiple module tasks concurrently within bounds.

        If `on_result` is provided, it is invoked immediately as each module finishes
        with (mod_id, findings, status_str), allowing real-time partial result accumulation.
        """

        async def _run_with_callback(
            module: OSINTModule, target: str, ctx: dict[str, Any]
        ) -> tuple[str, list[dict[str, Any]], str]:
            res = await self.run_single_module(module, target, ctx)
            if on_result is not None:
                try:
                    on_result(res[0], res[1], res[2])
                except Exception:
                    logger.exception(
                        "Error in scheduler on_result callback for module '%s'", res[0]
                    )
            return res

        futures = [_run_with_callback(module, target, ctx) for module, target, ctx in tasks]
        return await asyncio.gather(*futures)
