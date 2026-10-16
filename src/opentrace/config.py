"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment."""

    storage_mode: str = "memory"
    sqlite_path: str = "opentrace.db"
    max_concurrency: int = 5
    per_host_concurrency: int = 2
    default_timeout: float = 10.0
    max_runtime: float = 60.0
    max_findings_data_size: int = 10240
    log_level: str = "INFO"
    user_agent: str = "OpenTrace/0.1 (OSINT research tool)"


def load_settings() -> Settings:
    """Load settings from OPENTRACE_* environment variables."""
    return Settings(
        storage_mode=os.getenv("OPENTRACE_STORAGE_MODE", "memory"),
        sqlite_path=os.getenv("OPENTRACE_SQLITE_PATH", "opentrace.db"),
        max_concurrency=int(os.getenv("OPENTRACE_MAX_CONCURRENCY", "5")),
        per_host_concurrency=int(os.getenv("OPENTRACE_PER_HOST_CONCURRENCY", "2")),
        default_timeout=float(os.getenv("OPENTRACE_DEFAULT_TIMEOUT", "10.0")),
        max_runtime=float(os.getenv("OPENTRACE_MAX_RUNTIME", "60.0")),
        max_findings_data_size=int(os.getenv("OPENTRACE_MAX_FINDINGS_DATA_SIZE", "10240")),
        log_level=os.getenv("OPENTRACE_LOG_LEVEL", "INFO"),
        user_agent=os.getenv("OPENTRACE_USER_AGENT", "OpenTrace/0.1 (OSINT research tool)"),
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """Reset cached settings (useful for testing)."""
    global _settings
    _settings = None
