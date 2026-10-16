"""SQLite storage backend for persistent investigation records and user accounts."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from opentrace.storage.interface import StorageBackend
from opentrace.storage.migrations.runner import run_migrations


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class SQLiteStorage(StorageBackend):
    """Persistent SQLite-backed investigation and user storage with migrations."""

    def __init__(self, db_path: str = "opentrace.db") -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        run_migrations(self.db_path)

    def _sync_save(self, investigation: dict[str, Any], user_id: str | None = None) -> None:
        inv_id = str(investigation["id"])
        uid = user_id or investigation.get("user_id")
        created_at = str(investigation.get("created_at") or datetime.now(UTC).isoformat())
        status = str(investigation.get("status", "unknown"))

        req = investigation.get("request", {})
        target_type = None
        query = None
        if isinstance(req, dict):
            for k in ("username", "email", "phone", "name", "web", "query"):
                if req.get(k):
                    target_type = k
                    query = str(req[k])
                    break

        # Ensure user_id is in payload
        if uid and "user_id" not in investigation:
            investigation["user_id"] = uid

        payload = json.dumps(investigation, default=_json_serial)
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO investigations (id, user_id, created_at, status, target_type, query, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_id = coalesce(excluded.user_id, investigations.user_id),
                    status = excluded.status,
                    target_type = excluded.target_type,
                    query = excluded.query,
                    payload = excluded.payload
                """,
                (inv_id, uid, created_at, status, target_type, query, payload),
            )
            conn.commit()

    def _sync_get(self, investigation_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            if user_id is not None:
                cursor = conn.execute(
                    "SELECT payload FROM investigations WHERE id = ? AND user_id = ?",
                    (str(investigation_id), str(user_id)),
                )
            else:
                cursor = conn.execute(
                    "SELECT payload FROM investigations WHERE id = ? AND user_id IS NULL",
                    (str(investigation_id),),
                )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])  # type: ignore[no-any-return]
            return None

    def _sync_list(self, limit: int, user_id: str | None = None) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            if user_id is not None:
                cursor = conn.execute(
                    "SELECT payload FROM investigations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (str(user_id), limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT payload FROM investigations WHERE user_id IS NULL ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [json.loads(r[0]) for r in rows]

    def _sync_delete(self, investigation_id: str, user_id: str | None = None) -> bool:
        with self._get_conn() as conn:
            if user_id is not None:
                cursor = conn.execute(
                    "DELETE FROM investigations WHERE id = ? AND user_id = ?",
                    (str(investigation_id), str(user_id)),
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM investigations WHERE id = ? AND user_id IS NULL",
                    (str(investigation_id),),
                )
            conn.commit()
            return cursor.rowcount > 0

    def _sync_clear(self) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM investigations")
            conn.commit()

    async def save_investigation(
        self, investigation: dict[str, Any], user_id: str | None = None
    ) -> None:
        await asyncio.to_thread(self._sync_save, investigation, user_id)

    async def get_investigation(
        self, investigation_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get, investigation_id, user_id)

    async def list_investigations(
        self, limit: int = 20, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list, limit, user_id)

    async def delete_investigation(self, investigation_id: str, user_id: str | None = None) -> bool:
        return await asyncio.to_thread(self._sync_delete, investigation_id, user_id)

    async def clear(self) -> None:
        await asyncio.to_thread(self._sync_clear)

    # -------------------------------------------------------------------------
    # User Management Implementations
    # -------------------------------------------------------------------------
    def _row_to_user(self, row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "id": row[0],
            "email": row[1],
            "hashed_password": row[2],
            "name": row[3],
            "role": row[4],
            "is_active": bool(row[5]),
            "preferences": json.loads(row[6]) if isinstance(row[6], str) else row[6],
            "created_at": row[7],
            "updated_at": row[8],
        }

    def _sync_create_user(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        pref_str = json.dumps(user_dict.get("preferences", {}))
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_dict["id"],
                    user_dict["email"].strip().lower(),
                    user_dict["hashed_password"],
                    user_dict["name"].strip(),
                    user_dict.get("role", "user"),
                    1 if user_dict.get("is_active", True) else 0,
                    pref_str,
                    user_dict["created_at"],
                    user_dict["updated_at"],
                ),
            )
            conn.commit()
        return dict(user_dict)

    def _sync_get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at FROM users WHERE id = ?",
                (str(user_id),),
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def _sync_get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at FROM users WHERE email = ?",
                (email.strip().lower(),),
            )
            row = cursor.fetchone()
            return self._row_to_user(row) if row else None

    def _sync_update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        existing = self._sync_get_user_by_id(user_id)
        if not existing:
            return None

        fields: list[str] = []
        values: list[Any] = []
        for k, v in updates.items():
            if k in ("name", "hashed_password", "role"):
                fields.append(f"{k} = ?")
                values.append(v)
            elif k == "is_active":
                fields.append("is_active = ?")
                values.append(1 if v else 0)
            elif k == "preferences":
                fields.append("preferences = ?")
                values.append(json.dumps(v))

        if not fields:
            return existing

        fields.append("updated_at = ?")
        now_str = datetime.now(UTC).isoformat()
        values.append(now_str)
        values.append(str(user_id))

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                values,
            )
            conn.commit()

        return self._sync_get_user_by_id(user_id)

    def _sync_delete_user(self, user_id: str) -> bool:
        with self._get_conn() as conn:
            # Delete investigations owned by this user
            conn.execute("DELETE FROM investigations WHERE user_id = ?", (str(user_id),))
            conn.execute("DELETE FROM password_resets WHERE user_id = ?", (str(user_id),))
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (str(user_id),))
            conn.commit()
            return cursor.rowcount > 0

    async def create_user(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_create_user, user_dict)

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get_user_by_id, user_id)

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get_user_by_email, email)

    async def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_update_user, user_id, updates)

    async def delete_user(self, user_id: str) -> bool:
        return await asyncio.to_thread(self._sync_delete_user, user_id)

    # -------------------------------------------------------------------------
    # Password Reset Implementations
    # -------------------------------------------------------------------------
    def _sync_create_password_reset(self, reset_dict: dict[str, Any]) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO password_resets (token_hash, user_id, expires_at, used)
                VALUES (?, ?, ?, ?)
                """,
                (
                    reset_dict["token_hash"],
                    reset_dict["user_id"],
                    reset_dict["expires_at"],
                    1 if reset_dict.get("used", False) else 0,
                ),
            )
            conn.commit()

    def _sync_get_password_reset(self, token_hash: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT token_hash, user_id, expires_at, used FROM password_resets WHERE token_hash = ?",
                (token_hash,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "token_hash": row[0],
                    "user_id": row[1],
                    "expires_at": row[2],
                    "used": bool(row[3]),
                }
            return None

    def _sync_mark_password_reset_used(self, token_hash: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE password_resets SET used = 1 WHERE token_hash = ?",
                (token_hash,),
            )
            conn.commit()

    async def create_password_reset(self, reset_dict: dict[str, Any]) -> None:
        await asyncio.to_thread(self._sync_create_password_reset, reset_dict)

    async def get_password_reset(self, token_hash: str) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._sync_get_password_reset, token_hash)

    async def mark_password_reset_used(self, token_hash: str) -> None:
        await asyncio.to_thread(self._sync_mark_password_reset_used, token_hash)

    # -------------------------------------------------------------------------
    # Audit Event Implementations
    # -------------------------------------------------------------------------
    def _sync_create_audit(self, event_dict: dict[str, Any]) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, user_id, action, ip_address, created_at, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_dict["id"],
                    event_dict.get("user_id"),
                    event_dict["action"],
                    event_dict.get("ip_address"),
                    event_dict["created_at"],
                    json.dumps(event_dict.get("details", {}))
                    if isinstance(event_dict.get("details"), dict)
                    else event_dict.get("details"),
                ),
            )
            conn.commit()

    def _sync_list_audits(self, user_id: str | None, limit: int) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            if user_id:
                cursor = conn.execute(
                    "SELECT id, user_id, action, ip_address, created_at, details FROM audit_events WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT id, user_id, action, ip_address, created_at, details FROM audit_events ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                details = r[5]
                if (
                    details
                    and isinstance(details, str)
                    and (details.startswith("{") or details.startswith("["))
                ):
                    try:
                        details = json.loads(details)
                    except Exception:
                        pass
                results.append(
                    {
                        "id": r[0],
                        "user_id": r[1],
                        "action": r[2],
                        "ip_address": r[3],
                        "created_at": r[4],
                        "details": details,
                    }
                )
            return results

    async def create_audit_event(self, event_dict: dict[str, Any]) -> None:
        await asyncio.to_thread(self._sync_create_audit, event_dict)

    async def list_audit_events(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list_audits, user_id, limit)
