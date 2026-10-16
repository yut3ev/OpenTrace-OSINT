"""Authentication, password hashing, JWT management, and security utilities."""

from __future__ import annotations

import hashlib
import logging
import secrets
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from opentrace.config import get_settings
from opentrace.core.errors import OpenTraceError

logger = logging.getLogger("opentrace.core.auth")


class AuthenticationError(OpenTraceError):
    """Raised when authentication credentials are invalid or expired."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message)


class AuthorizationError(OpenTraceError):
    """Raised when an authenticated user attempts an unauthorized operation."""

    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(message)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt with standard salt rounds."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.warning("Error verifying password hash: %s", exc)
        return False


def create_access_token(
    subject: str,
    email: str,
    role: str = "user",
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token."""
    settings = get_settings()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Authentication token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid authentication token: {exc}") from exc


def generate_reset_token() -> str:
    """Generate a high-entropy cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a reset token using SHA-256 for secure storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthRateLimiter:
    """Simple in-memory sliding window rate limiter for login and registration."""

    def __init__(self, limit: int = 10, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        now = time.monotonic()
        history = self._attempts[identifier]
        # Keep attempts within sliding window
        self._attempts[identifier] = [t for t in history if now - t < self.window_seconds]
        if len(self._attempts[identifier]) >= self.limit:
            return False
        self._attempts[identifier].append(now)
        return True

    def reset(self) -> None:
        self._attempts.clear()


auth_rate_limiter = AuthRateLimiter(limit=10, window_seconds=60)
