"""Application configuration loaded from environment variables with alias normalization."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment with canonical and alias names."""

    storage_mode: str = "sqlite"
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
            "https://opentrace.vercel.app",
        ]
    )
    cors_origin_regex: str | None = None
    hibp_api_key: str | None = None
    numverify_api_key: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None

    # Auth & Database Settings
    require_auth: bool = False
    database_url: str | None = None
    jwt_secret: str = "opentrace-insecure-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    admin_email: str | None = None
    allow_registration: bool = True
    rate_limit_per_minute: int = 60
    auth_rate_limit_per_minute: int = 10


def load_settings() -> Settings:
    """Load settings from OPENTRACE_* environment variables, supporting canonical and alias keys."""
    # Storage setting: supports canonical OPENTRACE_STORAGE_MODE and alias OPENTRACE_STORAGE
    storage_mode = (
        os.getenv("OPENTRACE_STORAGE_MODE") or os.getenv("OPENTRACE_STORAGE") or "sqlite"
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
            "https://opentrace.vercel.app",
        ]
    cors_origin_regex = os.getenv("OPENTRACE_CORS_ORIGIN_REGEX")

    # Authorized Provider Keys
    hibp_api_key = os.getenv("HIBP_API_KEY")
    numverify_api_key = os.getenv("NUMVERIFY_API_KEY")
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    # Auth & Database Settings
    require_auth_raw = os.getenv("OPENTRACE_REQUIRE_AUTH", "false").lower()
    require_auth = require_auth_raw in ("1", "true", "yes", "on")
    database_url = os.getenv("DATABASE_URL") or os.getenv("OPENTRACE_DATABASE_URL")
    jwt_secret = (
        os.getenv("OPENTRACE_JWT_SECRET")
        or os.getenv("JWT_SECRET")
        or "opentrace-insecure-dev-secret-change-in-production"
    )
    jwt_algorithm = os.getenv("OPENTRACE_JWT_ALGORITHM", "HS256")
    expire_raw = os.getenv("OPENTRACE_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    access_token_expire_minutes = int(expire_raw)
    admin_email = os.getenv("OPENTRACE_ADMIN_EMAIL")
    allow_reg_raw = os.getenv("OPENTRACE_ALLOW_REGISTRATION", "true").lower()
    allow_registration = allow_reg_raw in ("1", "true", "yes", "on")
    rate_limit_per_minute = int(os.getenv("OPENTRACE_RATE_LIMIT_PER_MINUTE", "60"))
    auth_rate_limit_per_minute = int(os.getenv("OPENTRACE_AUTH_RATE_LIMIT_PER_MINUTE", "10"))

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
        cors_origin_regex=cors_origin_regex,
        hibp_api_key=hibp_api_key,
        numverify_api_key=numverify_api_key,
        twilio_account_sid=twilio_account_sid,
        twilio_auth_token=twilio_auth_token,
        require_auth=require_auth,
        database_url=database_url,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        admin_email=admin_email,
        allow_registration=allow_registration,
        rate_limit_per_minute=rate_limit_per_minute,
        auth_rate_limit_per_minute=auth_rate_limit_per_minute,
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
