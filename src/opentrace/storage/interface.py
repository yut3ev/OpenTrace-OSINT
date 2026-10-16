"""Abstract storage interface for investigations and user authentication."""

from __future__ import annotations

import abc
from typing import Any


class StorageBackend(abc.ABC):
    """Abstract storage backend for investigations, findings, users, and audits."""

    @abc.abstractmethod
    async def save_investigation(
        self, investigation: dict[str, Any], user_id: str | None = None
    ) -> None:
        """Persist or update an investigation record, optionally tied to a user."""
        ...

    @abc.abstractmethod
    async def get_investigation(
        self, investigation_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        """Retrieve an investigation by its UUID, enforcing user ownership if user_id is provided."""
        ...

    @abc.abstractmethod
    async def list_investigations(
        self, limit: int = 20, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List recent investigations, newest first, scoped to user_id if provided."""
        ...

    @abc.abstractmethod
    async def delete_investigation(self, investigation_id: str, user_id: str | None = None) -> bool:
        """Delete an investigation by ID, enforcing user ownership if user_id is provided."""
        ...

    @abc.abstractmethod
    async def clear(self) -> None:
        """Remove all investigations."""
        ...

    # User & Auth management
    @abc.abstractmethod
    async def create_user(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        """Create a new user account."""
        ...

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve a user by their unique ID."""
        ...

    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Retrieve a user by their lowercase email."""
        ...

    @abc.abstractmethod
    async def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update user fields (e.g. hashed_password, name, preferences, is_active)."""
        ...

    @abc.abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user account and associated records."""
        ...

    # Password reset tokens
    @abc.abstractmethod
    async def create_password_reset(self, reset_dict: dict[str, Any]) -> None:
        """Store a hashed password reset token with expiration."""
        ...

    @abc.abstractmethod
    async def get_password_reset(self, token_hash: str) -> dict[str, Any] | None:
        """Retrieve a password reset record by token hash."""
        ...

    @abc.abstractmethod
    async def mark_password_reset_used(self, token_hash: str) -> None:
        """Mark a password reset token as used."""
        ...

    # Audit events
    @abc.abstractmethod
    async def create_audit_event(self, event_dict: dict[str, Any]) -> None:
        """Record an audit trail event."""
        ...

    @abc.abstractmethod
    async def list_audit_events(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List audit events optionally filtered by user_id."""
        ...
