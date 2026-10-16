"""Application configuration loaded from environment variables with alias normalization."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment with canonical and alias names."""

    storage_mode: str = "memory"
    sqlite_path: str = "opentrace.db"
    max_concurrency: int = 5
    per_host_concurrency: int = 2
    default_timeout: float = 10.0
    max_runtime: float = 60.0
    max_findings_data_size: int = 10240
    log_level: str = "INFO"
    user_agent: str = "OpenTrace/0.1 (OSINT research tool)"
    api_key: str | None = None
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    hibp_api_key: str | None = None
    numverify_api_key: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None


def load_settings() -> Settings:
    """Load settings from OPENTRACE_* environment variables, supporting canonical and alias keys."""
    # Storage setting: supports canonical OPENTRACE_STORAGE_MODE and alias OPENTRACE_STORAGE
    storage_mode = (
        os.getenv("OPENTRACE_STORAGE_MODE") or os.getenv("OPENTRACE_STORAGE") or "memory"
    ).lower()

    # SQLite path
    sqlite_path = os.getenv("OPENTRACE_SQLITE_PATH", "opentrace.db")

    # Concurrency
    max_concurrency = int(os.getenv("OPENTRACE_MAX_CONCURRENCY", "5"))
    per_host_concurrency = int(os.getenv("OPENTRACE_PER_HOST_CONCURRENCY", "2"))

    # Request timeout: supports OPENTRACE_DEFAULT_TIMEOUT and OPENTRACE_REQUEST_TIMEOUT_SECONDS
    timeout_raw = (
        os.getenv("OPENTRACE_DEFAULT_TIMEOUT")
        or os.getenv("OPENTRACE_REQUEST_TIMEOUT_SECONDS")
        or "10.0"
    )
    default_timeout = float(timeout_raw)

    # Maximum investigation runtime: supports OPENTRACE_MAX_RUNTIME and OPENTRACE_MAX_RUNTIME_SECONDS
    runtime_raw = (
        os.getenv("OPENTRACE_MAX_RUNTIME") or os.getenv("OPENTRACE_MAX_RUNTIME_SECONDS") or "60.0"
    )
    max_runtime = float(runtime_raw)

    max_findings_data_size = int(os.getenv("OPENTRACE_MAX_FINDINGS_DATA_SIZE", "10240"))
    log_level = os.getenv("OPENTRACE_LOG_LEVEL", "INFO")
    user_agent = os.getenv("OPENTRACE_USER_AGENT", "OpenTrace/0.1 (OSINT research tool)")

    # API Security Key
    api_key = os.getenv("OPENTRACE_API_KEY")

    # CORS configuration
    cors_env = os.getenv("OPENTRACE_CORS_ORIGINS")
    if cors_env:
        cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    else:
        cors_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    # Authorized Provider Keys
    hibp_api_key = os.getenv("HIBP_API_KEY")
    numverify_api_key = os.getenv("NUMVERIFY_API_KEY")
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    return Settings(
        storage_mode=storage_mode,
        sqlite_path=sqlite_path,
        max_concurrency=max_concurrency,
        per_host_concurrency=per_host_concurrency,
        default_timeout=default_timeout,
        max_runtime=max_runtime,
        max_findings_data_size=max_findings_data_size,
        log_level=log_level,
        user_agent=user_agent,
        api_key=api_key,
        cors_origins=cors_origins,
        hibp_api_key=hibp_api_key,
        numverify_api_key=numverify_api_key,
        twilio_account_sid=twilio_account_sid,
        twilio_auth_token=twilio_auth_token,
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
