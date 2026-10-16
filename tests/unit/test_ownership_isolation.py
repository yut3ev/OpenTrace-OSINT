"""Tests verifying strict ownership isolation and anti-enumeration protections between users."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from opentrace.api.app import create_app
from opentrace.api.dependencies import get_storage, reset_dependencies
from opentrace.storage.memory import MemoryStorage


@pytest.mark.asyncio
async def test_cross_user_isolation_and_anti_enumeration() -> None:
    """Verify that User B cannot access, list, export, stream, or delete User A's investigations."""
    reset_dependencies()
    storage = MemoryStorage()
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register User A
        res_a = await client.post(
            "/api/v1/auth/register",
            json={"email": "alice@agency.org", "password": "AlicePassword123!", "name": "Alice"},
        )
        assert res_a.status_code == 201
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Register User B
        res_b = await client.post(
            "/api/v1/auth/register",
            json={"email": "bob@agency.org", "password": "BobPassword123!", "name": "Bob"},
        )
        assert res_b.status_code == 201
        token_b = res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A creates an investigation (with mock modules or empty module list)
        create_res = await client.post(
            "/api/v1/investigations",
            headers=headers_a,
            json={"username": "target_user_alice", "modules": []},
        )
        assert create_res.status_code == 200
        inv_id_a = create_res.json()["id"]

        # User A lists investigations -> sees 1 item
        list_a = await client.get("/api/v1/investigations", headers=headers_a)
        assert list_a.status_code == 200
        assert len(list_a.json()) == 1
        assert list_a.json()[0]["id"] == inv_id_a

        # User B lists investigations -> sees 0 items (strict isolation)
        list_b = await client.get("/api/v1/investigations", headers=headers_b)
        assert list_b.status_code == 200
        assert len(list_b.json()) == 0

        # User B attempts to fetch User A's investigation -> gets 404 (no enumeration)
        get_b = await client.get(f"/api/v1/investigations/{inv_id_a}", headers=headers_b)
        assert get_b.status_code == 404

        # User B attempts to export User A's investigation -> gets 404
        export_b = await client.get(
            f"/api/v1/investigations/{inv_id_a}/export?format=json",
            headers=headers_b,
        )
        assert export_b.status_code == 404

        # User B attempts to delete User A's investigation -> gets 404
        del_b = await client.delete(f"/api/v1/investigations/{inv_id_a}", headers=headers_b)
        assert del_b.status_code == 404

        # User B attempts to retry User A's investigation -> gets 404
        retry_b = await client.post(f"/api/v1/investigations/{inv_id_a}/retry", headers=headers_b)
        assert retry_b.status_code == 404

        # User B attempts to stream events from User A's investigation -> gets 404
        stream_b = await client.get(f"/api/v1/investigations/{inv_id_a}/events", headers=headers_b)
        assert stream_b.status_code == 404

        # Verify User A's investigation is still intact and accessible by User A
        get_a = await client.get(f"/api/v1/investigations/{inv_id_a}", headers=headers_a)
        assert get_a.status_code == 200
        assert get_a.json()["id"] == inv_id_a

        # Unauthenticated caller attempts to fetch, list, export, or delete User A's investigation -> gets 404
        get_unauth = await client.get(f"/api/v1/investigations/{inv_id_a}")
        assert get_unauth.status_code == 404

        list_unauth = await client.get("/api/v1/investigations")
        assert list_unauth.status_code == 200
        assert not any(item["id"] == inv_id_a for item in list_unauth.json())

        export_unauth = await client.get(f"/api/v1/investigations/{inv_id_a}/export?format=json")
        assert export_unauth.status_code == 404

        del_unauth = await client.delete(f"/api/v1/investigations/{inv_id_a}")
        assert del_unauth.status_code == 404


@pytest.mark.asyncio
async def test_require_auth_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    """When OPENTRACE_REQUIRE_AUTH is true, all unauthenticated investigation actions return 401."""
    monkeypatch.setenv("OPENTRACE_REQUIRE_AUTH", "true")
    reset_dependencies()
    storage = MemoryStorage()
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create unauth -> 401
        res = await client.post("/api/v1/investigations", json={"username": "testuser"})
        assert res.status_code == 401

        # List unauth -> 401
        res = await client.get("/api/v1/investigations")
        assert res.status_code == 401

        # Get unauth -> 401
        res = await client.get("/api/v1/investigations/non-existent-uuid")
        assert res.status_code == 401

        # Delete unauth -> 401
        res = await client.delete("/api/v1/investigations/non-existent-uuid")
        assert res.status_code == 401

        # Export unauth -> 401
        res = await client.get("/api/v1/investigations/non-existent-uuid/export")
        assert res.status_code == 401

