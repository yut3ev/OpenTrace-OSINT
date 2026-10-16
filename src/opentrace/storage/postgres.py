"""PostgreSQL storage backend for production persistent investigations and user accounts."""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.parse
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import psycopg2
from psycopg2 import pool

from opentrace.storage.interface import StorageBackend

logger = logging.getLogger("opentrace.storage.postgres")


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def normalize_postgres_url(url: str) -> str:
    """Normalize SQLAlchemy or cloud connection strings to standard psycopg2 DSN."""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if "+asyncpg" in scheme or "+psycopg2" in scheme:
        scheme = "postgresql"
    elif scheme == "postgres":
        scheme = "postgresql"

    # Enforce sslmode=require for non-local hosts if not already specified
    query_params = urllib.parse.parse_qs(parsed.query)
    is_local = parsed.hostname in ("localhost", "127.0.0.1", None)
    if not is_local and "sslmode" not in query_params:
        query_params["sslmode"] = ["require"]

    new_query = urllib.parse.urlencode(query_params, doseq=True)
    return urllib.parse.urlunparse(
        (scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


class PostgreSQLStorage(StorageBackend):
    """Production-grade PostgreSQL storage backend implementing the StorageBackend interface."""

    def __init__(self, database_url: str, min_conn: int = 1, max_conn: int = 10) -> None:
        self.raw_url = database_url
        self.dsn = normalize_postgres_url(database_url)
        self.min_conn = min_conn
        self.max_conn = max_conn
        self._pool: pool.ThreadedConnectionPool | None = None
        self._init_pool()
        self._init_db()

    def _init_pool(self) -> None:
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=self.min_conn,
                maxconn=self.max_conn,
                dsn=self.dsn,
            )
            logger.info("Initialized PostgreSQL connection pool successfully.")
        except Exception as exc:
            logger.error("Failed to initialize PostgreSQL connection pool: %s", exc)
            raise

    @contextmanager
    def _get_conn(self) -> Generator[psycopg2.extensions.connection, None, None]:
        if not self._pool:
            self._init_pool()
        assert self._pool is not None
        conn = self._pool.getconn()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            if self._pool and not conn.closed:
                self._pool.putconn(conn)

    def _init_db(self) -> None:
        """Run database migrations and ensure all tables and indexes exist."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version INTEGER PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        applied_at VARCHAR(100) NOT NULL
                    );
                    """
                )
                cur.execute("SELECT version FROM schema_migrations WHERE version = 1;")
                if not cur.fetchone():
                    logger.info("Applying PostgreSQL schema migration v1...")
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS users (
                            id VARCHAR(64) PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            hashed_password TEXT NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL DEFAULT 'user',
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            preferences TEXT NOT NULL DEFAULT '{}',
                            created_at VARCHAR(100) NOT NULL,
                            updated_at VARCHAR(100) NOT NULL
                        );
                        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

                        CREATE TABLE IF NOT EXISTS investigations (
                            id VARCHAR(64) PRIMARY KEY,
                            user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
                            created_at VARCHAR(100) NOT NULL,
                            status VARCHAR(50),
                            target_type VARCHAR(50),
                            query TEXT,
                            payload TEXT NOT NULL
                        );
                        CREATE INDEX IF NOT EXISTS idx_inv_user_created ON investigations(user_id, created_at DESC);
                        CREATE INDEX IF NOT EXISTS idx_inv_created_at ON investigations(created_at DESC);

                        CREATE TABLE IF NOT EXISTS password_resets (
                            token_hash VARCHAR(128) PRIMARY KEY,
                            user_id VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            expires_at VARCHAR(100) NOT NULL,
                            used BOOLEAN NOT NULL DEFAULT FALSE
                        );

                        CREATE TABLE IF NOT EXISTS audit_events (
                            id VARCHAR(64) PRIMARY KEY,
                            user_id VARCHAR(64),
                            action VARCHAR(100) NOT NULL,
                            ip_address VARCHAR(45),
                            created_at VARCHAR(100) NOT NULL,
                            details TEXT
                        );
                        CREATE INDEX IF NOT EXISTS idx_audit_user_created ON audit_events(user_id, created_at DESC);

                        INSERT INTO schema_migrations (version, name, applied_at)
                        VALUES (1, 'initial_schema_with_auth_and_isolation', %s)
                        ON CONFLICT (version) DO NOTHING;
                        """,
                        (datetime.now(UTC).isoformat(),),
                    )
            conn.commit()

    # -------------------------------------------------------------------------
    # Investigation Persistence
    # -------------------------------------------------------------------------
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

        if uid and "user_id" not in investigation:
            investigation["user_id"] = uid

        payload = json.dumps(investigation, default=_json_serial)
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO investigations (id, user_id, created_at, status, target_type, query, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
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
            with conn.cursor() as cur:
                if user_id is not None:
                    cur.execute(
                        "SELECT payload FROM investigations WHERE id = %s AND user_id = %s",
                        (str(investigation_id), str(user_id)),
                    )
                else:
                    cur.execute(
                        "SELECT payload FROM investigations WHERE id = %s AND user_id IS NULL",
                        (str(investigation_id),),
                    )
                row = cur.fetchone()
                if row:
                    return json.loads(row[0])  # type: ignore[no-any-return]
                return None

    def _sync_list(self, limit: int, user_id: str | None = None) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if user_id is not None:
                    cur.execute(
                        "SELECT payload FROM investigations WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                        (str(user_id), limit),
                    )
                else:
                    cur.execute(
                        "SELECT payload FROM investigations WHERE user_id IS NULL ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
                return [json.loads(r[0]) for r in rows]

    def _sync_delete(self, investigation_id: str, user_id: str | None = None) -> bool:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if user_id is not None:
                    cur.execute(
                        "DELETE FROM investigations WHERE id = %s AND user_id = %s",
                        (str(investigation_id), str(user_id)),
                    )
                else:
                    cur.execute(
                        "DELETE FROM investigations WHERE id = %s AND user_id IS NULL",
                        (str(investigation_id),),
                    )
                deleted = cur.rowcount > 0
            conn.commit()
        return bool(deleted)

    def _sync_clear(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM investigations")
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
            "preferences": json.loads(row[6]) if isinstance(row[6], str) else (row[6] or {}),
            "created_at": row[7],
            "updated_at": row[8],
        }

    def _sync_create_user(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        pref_str = json.dumps(user_dict.get("preferences", {}))
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_dict["id"],
                        user_dict["email"].strip().lower(),
                        user_dict["hashed_password"],
                        user_dict["name"].strip(),
                        user_dict.get("role", "user"),
                        bool(user_dict.get("is_active", True)),
                        pref_str,
                        user_dict["created_at"],
                        user_dict["updated_at"],
                    ),
                )
            conn.commit()
        return dict(user_dict)

    def _sync_get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at FROM users WHERE id = %s",
                    (str(user_id),),
                )
                row = cur.fetchone()
                return self._row_to_user(row) if row else None

    def _sync_get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, hashed_password, name, role, is_active, preferences, created_at, updated_at FROM users WHERE email = %s",
                    (email.strip().lower(),),
                )
                row = cur.fetchone()
                return self._row_to_user(row) if row else None

    def _sync_update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        existing = self._sync_get_user_by_id(user_id)
        if not existing:
            return None

        fields: list[str] = []
        values: list[Any] = []
        for k, v in updates.items():
            if k in ("name", "hashed_password", "role"):
                fields.append(f"{k} = %s")
                values.append(v)
            elif k == "is_active":
                fields.append("is_active = %s")
                values.append(bool(v))
            elif k == "preferences":
                fields.append("preferences = %s")
                values.append(json.dumps(v))

        if not fields:
            return existing

        fields.append("updated_at = %s")
        now_str = datetime.now(UTC).isoformat()
        values.append(now_str)
        values.append(str(user_id))

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE users SET {', '.join(fields)} WHERE id = %s",
                    values,
                )
            conn.commit()

        return self._sync_get_user_by_id(user_id)

    def _sync_delete_user(self, user_id: str) -> bool:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM investigations WHERE user_id = %s", (str(user_id),))
                cur.execute("DELETE FROM password_resets WHERE user_id = %s", (str(user_id),))
                cur.execute("DELETE FROM users WHERE id = %s", (str(user_id),))
                deleted = cur.rowcount > 0
            conn.commit()
        return bool(deleted)

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
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO password_resets (token_hash, user_id, expires_at, used)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        reset_dict["token_hash"],
                        str(reset_dict["user_id"]),
                        reset_dict["expires_at"],
                        bool(reset_dict.get("used", False)),
                    ),
                )
            conn.commit()

    def _sync_get_password_reset(self, token_hash: str) -> dict[str, Any] | None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT token_hash, user_id, expires_at, used FROM password_resets WHERE token_hash = %s",
                    (token_hash,),
                )
                row = cur.fetchone()
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
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE password_resets SET used = TRUE WHERE token_hash = %s",
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
    # Audit Events Implementations
    # -------------------------------------------------------------------------
    def _sync_create_audit_event(self, event_dict: dict[str, Any]) -> None:
        details_str = (
            json.dumps(event_dict["details"], default=_json_serial)
            if "details" in event_dict and event_dict["details"] is not None
            else None
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_events (id, user_id, action, ip_address, created_at, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        event_dict["id"],
                        str(event_dict["user_id"]) if event_dict.get("user_id") else None,
                        event_dict["action"],
                        event_dict.get("ip_address"),
                        event_dict["created_at"],
                        details_str,
                    ),
                )
            conn.commit()

    def _sync_list_audit_events(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        "SELECT id, user_id, action, ip_address, created_at, details FROM audit_events WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                        (str(user_id), limit),
                    )
                else:
                    cur.execute(
                        "SELECT id, user_id, action, ip_address, created_at, details FROM audit_events ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    )
                rows = cur.fetchall()
                results: list[dict[str, Any]] = []
                for row in rows:
                    details = json.loads(row[5]) if row[5] else None
                    results.append(
                        {
                            "id": row[0],
                            "user_id": row[1],
                            "action": row[2],
                            "ip_address": row[3],
                            "created_at": row[4],
                            "details": details,
                        }
                    )
                return results

    async def create_audit_event(self, event_dict: dict[str, Any]) -> None:
        await asyncio.to_thread(self._sync_create_audit_event, event_dict)

    async def list_audit_events(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._sync_list_audit_events, user_id, limit)
