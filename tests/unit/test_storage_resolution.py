"""Unit tests for get_storage dependency resolution."""

from unittest.mock import patch

from opentrace.api.dependencies import get_storage, reset_dependencies
from opentrace.config import Settings
from opentrace.storage.memory import MemoryStorage
from opentrace.storage.sqlite import SQLiteStorage


def test_get_storage_sqlite(tmp_path):
    """Test resolution to SQLiteStorage when storage_mode='sqlite'."""
    reset_dependencies()
    db_file = str(tmp_path / "resolve.db")
    settings = Settings(storage_mode="sqlite", sqlite_path=db_file)
    store = get_storage(settings)
    assert isinstance(store, SQLiteStorage)


def test_get_storage_memory():
    """Test resolution to MemoryStorage when storage_mode='memory'."""
    reset_dependencies()
    settings = Settings(storage_mode="memory")
    store = get_storage(settings)
    assert isinstance(store, MemoryStorage)


def test_get_storage_postgres():
    """Test resolution to PostgreSQLStorage when database_url is provided."""
    reset_dependencies()
    settings = Settings(
        storage_mode="postgres",
        database_url="postgresql://user:pass@localhost:5432/opentrace",
    )
    with (
        patch("opentrace.storage.postgres.PostgreSQLStorage._init_pool"),
        patch("opentrace.storage.postgres.PostgreSQLStorage._init_db"),
    ):
        store = get_storage(settings)
        from opentrace.storage.postgres import PostgreSQLStorage

        assert isinstance(store, PostgreSQLStorage)
