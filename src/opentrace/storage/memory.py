"""In-memory storage backend with user management and ownership support."""

from __future__ import annotations

import asyncio
import copy
from datetime import UTC, datetime
from typing import Any

from opentrace.storage.interface import StorageBackend


class MemoryStorage(StorageBackend):
    """Volatile in-memory storage backend with thread-safe locking and capacity limits."""

    def __init__(self, max_capacity: int = 1000) -> None:
        self._storage: dict[str, dict[str, Any]] = {}
        self._users: dict[str, dict[str, Any]] = {}
        self._password_resets: dict[str, dict[str, Any]] = {}
        self._audit_events: list[dict[str, Any]] = []
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def save_investigation(
        self, investigation: dict[str, Any], user_id: str | None = None
    ) -> None:
        async with self._lock:
            inv_id = str(investigation["id"])
            if user_id and "user_id" not in investigation:
                investigation["user_id"] = user_id
            if inv_id not in self._storage and len(self._storage) >= self._max_capacity:
                oldest_key = next(iter(self._storage))
                del self._storage[oldest_key]
            self._storage[inv_id] = copy.deepcopy(investigation)

    async def get_investigation(
        self, investigation_id: str, user_id: str | None = None
    ) -> dict[str, Any] | None:
        async with self._lock:
            item = self._storage.get(str(investigation_id))
            if not item:
                return None
            if user_id is not None:
                if item.get("user_id") != user_id:
                    return None
            else:
                if item.get("user_id") is not None:
                    return None
            return copy.deepcopy(item)

    async def list_investigations(
        self, limit: int = 20, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        async with self._lock:
            items = list(self._storage.values())
            if user_id is not None:
                items = [item for item in items if item.get("user_id") == user_id]
            else:
                items = [item for item in items if item.get("user_id") is None]
            items.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
            return copy.deepcopy(items[:limit])

    async def delete_investigation(self, investigation_id: str, user_id: str | None = None) -> bool:
        async with self._lock:
            key = str(investigation_id)
            if key in self._storage:
                if user_id is not None:
                    if self._storage[key].get("user_id") != user_id:
                        return False
                else:
                    if self._storage[key].get("user_id") is not None:
                        return False
                del self._storage[key]
                return True
            return False

    async def clear(self) -> None:
        async with self._lock:
            self._storage.clear()
            self._users.clear()
            self._password_resets.clear()
            self._audit_events.clear()

    # User Management
    async def create_user(self, user_dict: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            email_lower = user_dict["email"].strip().lower()
            for u in self._users.values():
                if u["email"].lower() == email_lower:
                    raise ValueError(f"User with email '{email_lower}' already exists")
            self._users[user_dict["id"]] = copy.deepcopy(user_dict)
            return copy.deepcopy(user_dict)

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        async with self._lock:
            u = self._users.get(str(user_id))
            return copy.deepcopy(u) if u else None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        async with self._lock:
            email_lower = email.strip().lower()
            for u in self._users.values():
                if u["email"].lower() == email_lower:
                    return copy.deepcopy(u)
            return None

    async def update_user(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        async with self._lock:
            u = self._users.get(str(user_id))
            if not u:
                return None
            for k, v in updates.items():
                u[k] = copy.deepcopy(v)
            u["updated_at"] = datetime.now(UTC).isoformat()
            return copy.deepcopy(u)

    async def delete_user(self, user_id: str) -> bool:
        async with self._lock:
            uid = str(user_id)
            if uid in self._users:
                del self._users[uid]
                # Delete user investigations
                to_del = [k for k, v in self._storage.items() if v.get("user_id") == uid]
                for k in to_del:
                    del self._storage[k]
                return True
            return False

    # Password Resets
    async def create_password_reset(self, reset_dict: dict[str, Any]) -> None:
        async with self._lock:
            self._password_resets[reset_dict["token_hash"]] = copy.deepcopy(reset_dict)

    async def get_password_reset(self, token_hash: str) -> dict[str, Any] | None:
        async with self._lock:
            pr = self._password_resets.get(token_hash)
            return copy.deepcopy(pr) if pr else None

    async def mark_password_reset_used(self, token_hash: str) -> None:
        async with self._lock:
            if token_hash in self._password_resets:
                self._password_resets[token_hash]["used"] = True

    # Audit Events
    async def create_audit_event(self, event_dict: dict[str, Any]) -> None:
        async with self._lock:
            self._audit_events.append(copy.deepcopy(event_dict))

    async def list_audit_events(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        async with self._lock:
            events = self._audit_events
            if user_id:
                events = [e for e in events if e.get("user_id") == user_id]
            sorted_events = sorted(events, key=lambda x: str(x.get("created_at", "")), reverse=True)
            return copy.deepcopy(sorted_events[:limit])
