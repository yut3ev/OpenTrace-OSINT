"""Unit tests for Memory and SQLite storage implementations."""

import pytest

from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage


@pytest.mark.asyncio
async def test_memory_storage_crud():
    store = MemoryStorage(max_capacity=5)
    inv = {"id": "test-1", "created_at": "2026-01-01T00:00:00Z", "status": "completed"}

    await store.save_investigation(inv)
    fetched = await store.get_investigation("test-1")
    assert fetched is not None
    assert fetched["id"] == "test-1"

    items = await store.list_investigations()
    assert len(items) == 1

    deleted = await store.delete_investigation("test-1")
    assert deleted is True
    assert await store.get_investigation("test-1") is None


@pytest.mark.asyncio
async def test_memory_storage_capacity_eviction():
    store = MemoryStorage(max_capacity=2)
    await store.save_investigation({"id": "inv-1", "created_at": "2026-01-01T00:00:00Z"})
    await store.save_investigation({"id": "inv-2", "created_at": "2026-01-01T00:01:00Z"})
    await store.save_investigation({"id": "inv-3", "created_at": "2026-01-01T00:02:00Z"})

    # inv-1 should have been evicted
    assert await store.get_investigation("inv-1") is None
    assert await store.get_investigation("inv-2") is not None
    assert await store.get_investigation("inv-3") is not None


@pytest.mark.asyncio
async def test_sqlite_storage_crud(tmp_path):
    db_path = str(tmp_path / "test.db")
    store = SQLiteStorage(db_path)
    inv = {
        "id": "sql-1",
        "created_at": "2026-01-01T12:00:00Z",
        "status": "completed",
        "findings": [{"id": "f1", "status": "found"}],
    }

    await store.save_investigation(inv)
    fetched = await store.get_investigation("sql-1")
    assert fetched is not None
    assert fetched["id"] == "sql-1"
    assert len(fetched["findings"]) == 1

    items = await store.list_investigations(limit=10)
    assert len(items) == 1

    deleted = await store.delete_investigation("sql-1")
    assert deleted is True
    assert await store.get_investigation("sql-1") is None
