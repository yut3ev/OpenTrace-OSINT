"""Base definitions and interfaces for OSINT modules."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from opentrace.api.schemas.common import TargetType


@dataclass
class ModuleMetadata:
    """Metadata describing an OSINT module's identity and capabilities."""

    id: str
    name: str
    version: str
    supported_targets: list[TargetType]
    source_name: str
    source_url: str
    description: str
    enabled: bool = True
    implementation_status: str = "implemented"  # implemented, planned, disabled
    limitations: list[str] = field(default_factory=list)
    timeout: float = 10.0
    max_requests: int = 5
    rate_limit_per_second: float = 1.0


class OSINTModule(abc.ABC):
    """Abstract base class for all OSINT collection modules."""

    @property
    @abc.abstractmethod
    def metadata(self) -> ModuleMetadata:
        """Module metadata declaration."""
        ...

    @abc.abstractmethod
    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute the module against a normalized target identifier.

        Returns a list of raw finding dictionaries.
        """
        ...

    def supports(self, target_type: TargetType | str) -> bool:
        """Check if target type is supported by this module."""
        val = target_type.value if isinstance(target_type, TargetType) else target_type
        return any(t.value == val for t in self.metadata.supported_targets)
