"""Database migration runner and schema versioning for OpenTrace."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger("opentrace.storage.migrations")


@dataclass(frozen=True)
class SchemaMigration:
    """Represents an atomic, versioned database schema migration."""

    version: int
    name: str
    up: list[str]


MIGRATIONS: list[SchemaMigration] = [
    # Version 1: Core tables (users, investigations with user_id, password_resets, audit_events)
    SchemaMigration(
        version=1,
        name="initial_schema_with_auth_and_isolation",
        up=[
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                preferences TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """,
            """
            CREATE TABLE IF NOT EXISTS investigations (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL,
                status TEXT,
                target_type TEXT,
                query TEXT,
                payload TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_inv_user_created ON investigations(user_id, created_at DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_inv_created_at ON investigations(created_at DESC);
            """,
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                action TEXT NOT NULL,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                details TEXT
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_audit_user_created ON audit_events(user_id, created_at DESC);
            """,
        ],
    )
]


def run_migrations(db_path: str) -> int:
    """Apply any pending schema migrations to SQLite database. Returns highest version applied."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
            """
        )
        conn.commit()

        cursor = conn.execute("SELECT version FROM schema_migrations")
        applied_versions = {row[0] for row in cursor.fetchall()}

        # Check existing investigations table for backwards compatibility schema upgrades
        cur = conn.execute("PRAGMA table_info(investigations);")
        columns = [row[1] for row in cur.fetchall()]
        if columns and "user_id" not in columns:
            logger.info(
                "Migrating legacy investigations table: adding user_id, status, target_type, query"
            )
            try:
                conn.execute("ALTER TABLE investigations ADD COLUMN user_id TEXT;")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE investigations ADD COLUMN status TEXT;")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE investigations ADD COLUMN target_type TEXT;")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE investigations ADD COLUMN query TEXT;")
            except sqlite3.OperationalError:
                pass
            conn.commit()

        highest = max(applied_versions) if applied_versions else 0
        for migration in MIGRATIONS:
            if migration.version not in applied_versions:
                logger.info("Applying migration v%s: %s", migration.version, migration.name)
                for stmt in migration.up:
                    conn.execute(stmt)
                now_str = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (migration.version, migration.name, now_str),
                )
                conn.commit()
                highest = migration.version

        return highest
    finally:
        conn.close()
