"""In-memory storage backend."""

from __future__ import annotations

import asyncio
import copy
from typing import Any

from opentrace.storage.interface import StorageBackend


class MemoryStorage(StorageBackend):
    """Volatile in-memory storage backend with thread-safe locking and capacity limits."""

    def __init__(self, max_capacity: int = 1000) -> None:
        self._storage: dict[str, dict[str, Any]] = {}
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def save_investigation(self, investigation: dict[str, Any]) -> None:
        async with self._lock:
            inv_id = str(investigation["id"])
            if inv_id not in self._storage and len(self._storage) >= self._max_capacity:
                # Evict oldest entry (FIFO)
                oldest_key = next(iter(self._storage))
                del self._storage[oldest_key]
            self._storage[inv_id] = copy.deepcopy(investigation)

    async def get_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        async with self._lock:
            item = self._storage.get(str(investigation_id))
            return copy.deepcopy(item) if item else None

    async def list_investigations(self, limit: int = 20) -> list[dict[str, Any]]:
        async with self._lock:
            items = list(self._storage.values())
            # Sort newest first based on created_at
            items.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
            return copy.deepcopy(items[:limit])

    async def delete_investigation(self, investigation_id: str) -> bool:
        async with self._lock:
            key = str(investigation_id)
            if key in self._storage:
                del self._storage[key]
                return True
            return False

    async def clear(self) -> None:
        async with self._lock:
            self._storage.clear()
