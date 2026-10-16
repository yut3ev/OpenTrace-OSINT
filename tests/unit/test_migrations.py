"""Unit tests for SQLite schema migration runner and persistence."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from opentrace.storage.migrations.runner import run_migrations
from opentrace.storage.sqlite import SQLiteStorage


def test_migrations_runner_creates_schema_and_is_idempotent() -> None:
    """Verify that run_migrations creates all tables and can run repeatedly without error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_migration.db")

        # Initial run
        highest_v = run_migrations(db_path)
        assert highest_v >= 1

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Check tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        assert "schema_migrations" in tables
        assert "users" in tables
        assert "investigations" in tables
        assert "password_resets" in tables
        assert "audit_events" in tables

        # Second run (idempotency check)
        second_v = run_migrations(db_path)
        assert second_v == highest_v
        conn.close()


@pytest.mark.asyncio
async def test_sqlite_user_and_investigation_isolation() -> None:
    """Verify user persistence and scoped investigation queries in SQLiteStorage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_storage.db")
        storage = SQLiteStorage(db_path)

        # Create user
        user_a = {
            "id": "u-alice-1",
            "email": "alice@test.com",
            "hashed_password": "hash_alice_pwd",
            "name": "Alice Analyst",
            "role": "user",
            "is_active": True,
            "preferences": {"theme": "dark"},
            "created_at": "2026-10-16T12:00:00Z",
            "updated_at": "2026-10-16T12:00:00Z",
        }
        await storage.create_user(user_a)

        # Retrieve user by email
        fetched = await storage.get_user_by_email("ALICE@test.com")
        assert fetched is not None
        assert fetched["id"] == "u-alice-1"
        assert fetched["preferences"]["theme"] == "dark"

        # Save investigation for user_a
        inv_a = {
            "id": "inv-alice-99",
            "user_id": "u-alice-1",
            "created_at": "2026-10-16T12:10:00Z",
            "status": "completed",
            "request": {"username": "target_alpha"},
            "findings": [{"id": "f1", "title": "GitHub match", "status": "found"}],
        }
        await storage.save_investigation(inv_a, user_id="u-alice-1")

        # Query with user_a -> found
        res_a = await storage.get_investigation("inv-alice-99", user_id="u-alice-1")
        assert res_a is not None
        assert res_a["id"] == "inv-alice-99"

        # Query with user_b -> None
        res_b = await storage.get_investigation("inv-alice-99", user_id="u-bob-2")
        assert res_b is None

        # List investigations for user_a vs user_b
        list_a = await storage.list_investigations(user_id="u-alice-1")
        assert len(list_a) == 1
        list_b = await storage.list_investigations(user_id="u-bob-2")
        assert len(list_b) == 0

        # Audit events
        await storage.create_audit_event(
            {
                "id": "audit-1",
                "user_id": "u-alice-1",
                "action": "investigation.created",
                "ip_address": "127.0.0.1",
                "created_at": "2026-10-16T12:11:00Z",
                "details": {"investigation_id": "inv-alice-99"},
            }
        )
        audits = await storage.list_audit_events(user_id="u-alice-1")
        assert len(audits) == 1
        assert audits[0]["action"] == "investigation.created"
