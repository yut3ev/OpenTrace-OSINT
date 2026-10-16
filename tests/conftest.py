"""Pytest configuration and common fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from opentrace.api.app import create_app
from opentrace.api.dependencies import reset_dependencies
from opentrace.config import Settings, reset_settings
from opentrace.core.events import EventBus
from opentrace.modules.registry import ModuleRegistry, get_default_registry
from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage


@pytest.fixture(autouse=True)
def setup_teardown(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Ensure clean global dependency states for every test."""
    monkeypatch.setenv("OPENTRACE_STORAGE_MODE", "memory")
    reset_settings()
    reset_dependencies()
    yield
    reset_settings()
    reset_dependencies()


@pytest.fixture
def test_settings() -> Settings:
    """Return test-specific settings."""
    return Settings(
        storage_mode="memory",
        max_concurrency=3,
        per_host_concurrency=1,
        default_timeout=2.0,
        max_runtime=5.0,
    )


@pytest.fixture
def memory_storage() -> MemoryStorage:
    """Provide a fresh in-memory storage."""
    return MemoryStorage()


@pytest.fixture
def sqlite_storage(tmp_path: pytest.TempPathFactory) -> SQLiteStorage:
    """Provide a temporary SQLite storage."""
    db_file = str(tmp_path / "test_opentrace.db")
    return SQLiteStorage(db_file)


@pytest.fixture
def registry() -> ModuleRegistry:
    """Provide default populated registry."""
    return get_default_registry()


@pytest.fixture
def event_bus() -> EventBus:
    """Provide fresh event bus."""
    return EventBus()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient for FastAPI testing via ASGI transport."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
