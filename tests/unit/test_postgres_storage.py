"""Unit tests for PostgreSQL storage implementation and URL normalization."""

from unittest.mock import MagicMock, patch

import pytest

from opentrace.storage.postgres import PostgreSQLStorage, normalize_postgres_url


def test_normalize_postgres_url():
    """Verify conversion of legacy/SQLAlchemy schemes and SSL mode defaults."""
    # Cloud postgres URL -> postgresql with sslmode=require
    cloud_url = "postgres://user:secret@dpg-abc123-a.oregon-postgres.render.com/opentrace_db"
    normalized = normalize_postgres_url(cloud_url)
    assert normalized.startswith("postgresql://")
    assert "sslmode=require" in normalized

    # asyncpg scheme normalization
    asyncpg_url = "postgresql+asyncpg://user:secret@remote-host.com:5432/opentrace"
    normalized_asyncpg = normalize_postgres_url(asyncpg_url)
    assert normalized_asyncpg.startswith("postgresql://")
    assert "sslmode=require" in normalized_asyncpg

    # Localhost connection preserves non-SSL
    local_url = "postgresql://user:secret@localhost:5432/opentrace"
    normalized_local = normalize_postgres_url(local_url)
    assert "sslmode=require" not in normalized_local

    # Pre-existing sslmode parameter is preserved
    explicit_ssl = "postgres://user:secret@remote-host.com/db?sslmode=verify-full"
    normalized_explicit = normalize_postgres_url(explicit_ssl)
    assert "sslmode=verify-full" in normalized_explicit


@pytest.mark.asyncio
async def test_postgres_storage_mocked_operations():
    """Verify PostgreSQLStorage database queries using mocked psycopg2 pool."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.closed = False

    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    with (
        patch("opentrace.storage.postgres.pool.ThreadedConnectionPool", return_value=mock_pool),
        patch("opentrace.storage.postgres.PostgreSQLStorage._init_db"),
    ):
        store = PostgreSQLStorage("postgresql://user:pass@localhost:5432/testdb")

        # Save investigation
        inv = {
            "id": "pg-inv-1",
            "created_at": "2026-01-01T00:00:00Z",
            "status": "completed",
            "request": {"username": "testuser"},
        }
        await store.save_investigation(inv, user_id="user-123")
        assert mock_cursor.execute.called

        # Get investigation
        mock_cursor.fetchone.return_value = (
            '{"id": "pg-inv-1", "status": "completed", "user_id": "user-123"}',
        )
        res = await store.get_investigation("pg-inv-1", user_id="user-123")
        assert res is not None
        assert res["id"] == "pg-inv-1"

        # List investigations
        mock_cursor.fetchall.return_value = [
            ('{"id": "pg-inv-1", "status": "completed"}',),
        ]
        items = await store.list_investigations(limit=10, user_id="user-123")
        assert len(items) == 1
        assert items[0]["id"] == "pg-inv-1"

        # Delete investigation
        mock_cursor.rowcount = 1
        deleted = await store.delete_investigation("pg-inv-1", user_id="user-123")
        assert deleted is True

        # Clear
        await store.clear()
        assert mock_cursor.execute.called
