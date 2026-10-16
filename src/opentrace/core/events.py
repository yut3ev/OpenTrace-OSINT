"""Event system for investigation progress reporting."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("opentrace.events")


class EventType(StrEnum):
    """Types of events emitted during investigation."""

    investigation_started = "investigation.started"
    module_started = "module.started"
    finding_created = "finding.created"
    module_completed = "module.completed"
    module_failed = "module.failed"
    investigation_completed = "investigation.completed"
    investigation_cancelled = "investigation.cancelled"


@dataclass
class Event:
    """An investigation lifecycle event."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Type for async event callbacks
EventCallback = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Publish-subscribe event bus for investigation events.

    Supports multiple async subscribers. Errors in subscribers are logged
    but do not crash the publisher.
    """

    def __init__(self) -> None:
        self._subscribers: list[EventCallback] = []
        self._lock = asyncio.Lock()

    async def subscribe(self, callback: EventCallback) -> None:
        """Register an async event callback."""
        async with self._lock:
            self._subscribers.append(callback)

    async def unsubscribe(self, callback: EventCallback) -> None:
        """Remove an event callback."""
        async with self._lock:
            self._subscribers = [s for s in self._subscribers if s is not callback]

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        async with self._lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            try:
                await subscriber(event)
            except Exception:
                logger.exception("Error in event subscriber for %s", event.type)

    async def clear(self) -> None:
        """Remove all subscribers."""
        async with self._lock:
            self._subscribers.clear()
