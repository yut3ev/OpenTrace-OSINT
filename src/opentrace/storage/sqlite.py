"""SQLite storage backend for persistent investigation records."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from opentrace.storage.interface import StorageBackend


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class SQLiteStorage(StorageBackend):
    """Persistent SQLite-backed investigation storage."""

    def __init__(self, db_path: str = "opentrace.db") -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_inv_created_at ON investigations (created_at DESC)"
            )
            conn.commit()

    def _sync_save(self, investigation: dict[str, Any]) -> None:
        inv_id = str(investigation["id"])
        created_at = str(investigation.get("created_at", ""))
        payload = json.dumps(investigation, default=_json_serial)
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO investigations (id, created_at, payload)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    payload = excluded.payload
                """,
                (inv_id, created_at, payload),
            )
            conn.commit()

    def _sync_get(self, investigation_id: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT payload FROM investigations WHERE id = ?", (str(investigation_id),)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])  # type: ignore[no-any-return]
            return None

    def _sync_list(self, limit: int) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT payload FROM investigations ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            return [json.loads(r[0]) for r in rows]

    def _sync_delete(self, investigation_id: str) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM investigations WHERE id = ?", (str(investigation_id),)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _sync_clear(self) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM investigations")
            conn.commit()

    async def save_investigation(self, investigation: dict[str, Any]) -> None:
        await asyncio.to_thread(self._sync_save, investigation)

    async def get_investigation(self, investigation_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get, investigation_id)

    async def list_investigations(self, limit: int = 20) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list, limit)

    async def delete_investigation(self, investigation_id: str) -> bool:
        return await asyncio.to_thread(self._sync_delete, investigation_id)

    async def clear(self) -> None:
        await asyncio.to_thread(self._sync_clear)
