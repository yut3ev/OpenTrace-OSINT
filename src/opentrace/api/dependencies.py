"""FastAPI dependency injection providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from opentrace.config import Settings, get_settings
from opentrace.core.events import EventBus
from opentrace.core.orchestrator import InvestigationOrchestrator
from opentrace.core.scheduler import BoundedScheduler
from opentrace.modules.registry import ModuleRegistry, get_default_registry
from opentrace.storage.interface import StorageBackend
from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage

_storage_instance: StorageBackend | None = None
_event_bus_instance: EventBus | None = None
_scheduler_instance: BoundedScheduler | None = None
_orchestrator_instance: InvestigationOrchestrator | None = None


def get_app_settings() -> Settings:
    """Return the global settings instance."""
    return get_settings()


def get_storage(settings: Annotated[Settings, Depends(get_app_settings)]) -> StorageBackend:
    """Provide the storage backend singleton."""
    global _storage_instance
    if _storage_instance is None:
        if settings.storage_mode == "sqlite":
            _storage_instance = SQLiteStorage(settings.sqlite_path)
        else:
            _storage_instance = MemoryStorage()
    return _storage_instance


def get_event_bus() -> EventBus:
    """Provide the event bus singleton."""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def get_registry() -> ModuleRegistry:
    """Provide the module registry singleton."""
    return get_default_registry()


def get_scheduler(
    settings: Annotated[Settings, Depends(get_app_settings)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
) -> BoundedScheduler:
    """Provide the scheduler singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = BoundedScheduler(
            global_concurrency=settings.max_concurrency,
            per_host_concurrency=settings.per_host_concurrency,
            event_bus=event_bus,
        )
    return _scheduler_instance


def get_orchestrator(
    storage: Annotated[StorageBackend, Depends(get_storage)],
    registry: Annotated[ModuleRegistry, Depends(get_registry)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    scheduler: Annotated[BoundedScheduler, Depends(get_scheduler)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> InvestigationOrchestrator:
    """Provide the orchestrator singleton."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = InvestigationOrchestrator(
            storage=storage,
            registry=registry,
            event_bus=event_bus,
            scheduler=scheduler,
            settings=settings,
        )
    return _orchestrator_instance


def reset_dependencies() -> None:
    """Reset dependency singletons (useful in testing suites)."""
    global _storage_instance, _event_bus_instance, _scheduler_instance, _orchestrator_instance
    _storage_instance = None
    _event_bus_instance = None
    _scheduler_instance = None
    _orchestrator_instance = None
