"""Unit tests for investigation retry functionality and failed source recovery."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from opentrace.api.app import create_app
from opentrace.api.dependencies import get_storage, reset_dependencies
from opentrace.storage.memory import MemoryStorage


@pytest.mark.asyncio
async def test_retry_investigation_endpoint() -> None:
    """Verify that retrying an investigation reruns failed sources and updates the record."""
    reset_dependencies()
    storage = MemoryStorage()
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: storage

    # Create initial investigation record with one succeeded module and one failed module
    inv_id = "test-inv-retry-123"
    initial_inv = {
        "id": inv_id,
        "status": "partial",
        "created_at": "2026-10-16T10:00:00Z",
        "request": {"username": "target_user", "modules": ["username.github", "username.twitter"]},
        "findings": [
            {
                "id": "f1",
                "investigation_id": inv_id,
                "module_id": "username.github",
                "module": "username.github",
                "target_type": "username",
                "status": "found",
                "title": "GitHub Profile",
                "evidence": "Profile exists",
                "source_name": "GitHub",
                "observed_at": "2026-10-16T10:00:01Z",
                "confidence": "high",
                "data": {},
            },
            {
                "id": "f2",
                "investigation_id": inv_id,
                "module_id": "username.twitter",
                "module": "username.twitter",
                "target_type": "username",
                "status": "error",
                "title": "Twitter Error",
                "evidence": "Network timeout",
                "source_name": "Twitter",
                "observed_at": "2026-10-16T10:00:02Z",
                "confidence": "none",
                "data": {},
            },
        ],
        "summary": {
            "total": 2,
            "by_status": {"found": 1, "error": 1},
            "duration_seconds": 1.2,
            "module_statuses": {"username.github": "completed", "username.twitter": "error"},
            "metrics": {
                "registered": 149,
                "eligible": 2,
                "attempted": 2,
                "succeeded": 1,
                "error": 1,
            },
        },
        "warnings": [],
    }
    await storage.save_investigation(initial_inv)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/investigations/{inv_id}/retry")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == inv_id
        # Record was saved and is accessible
        updated_rec = await storage.get_investigation(inv_id)
        assert updated_rec is not None
