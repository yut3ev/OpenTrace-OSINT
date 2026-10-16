"""Abstract storage interface for investigations."""

from __future__ import annotations

import abc
from typing import Any


class StorageBackend(abc.ABC):
    """Abstract storage backend for investigations and findings."""

    @abc.abstractmethod
    async def save_investigation(self, investigation: dict[str, Any]) -> None:
        """Persist or update an investigation record."""
        ...

    @abc.abstractmethod
    async def get_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        """Retrieve an investigation by its UUID."""
        ...

    @abc.abstractmethod
    async def list_investigations(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent investigations, newest first."""
        ...

    @abc.abstractmethod
    async def delete_investigation(self, investigation_id: str) -> bool:
        """Delete an investigation by its ID. Returns True if found and deleted."""
        ...

    @abc.abstractmethod
    async def clear(self) -> None:
        """Remove all investigations."""
        ...
