"""Integration tests for REST API routes."""

import pytest
import respx
from httpx import AsyncClient, Response


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    res = await async_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "storage_mode" in data


@pytest.mark.asyncio
async def test_list_modules_endpoint(async_client: AsyncClient):
    res = await async_client.get("/api/v1/modules")
    assert res.status_code == 200
    modules = res.json()
    assert len(modules) >= 5
    ids = {m["id"] for m in modules}
    assert "username.github" in ids
    assert "email.syntax" in ids
    assert "phone.numbering" in ids


@pytest.mark.asyncio
@respx.mock
async def test_investigation_lifecycle_api(async_client: AsyncClient):
    # Mock GitHub
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=Response(
            200,
            json={"login": "octocat", "name": "Octocat", "html_url": "https://github.com/octocat"},
        )
    )
    # Mock GitLab
    respx.get("https://gitlab.com/api/v4/users?username=octocat").mock(
        return_value=Response(200, json=[])
    )

    # 1. Create investigation
    create_res = await async_client.post(
        "/api/v1/investigations",
        json={"username": "octocat"},
    )
    assert create_res.status_code == 200
    data = create_res.json()
    inv_id = data["id"]
    assert data["status"] in ("completed", "partial")
    assert len(data["findings"]) >= 2

    # 2. List investigations
    list_res = await async_client.get("/api/v1/investigations")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == inv_id for item in items)

    # 3. Get single investigation
    get_res = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == inv_id

    # 4. Delete investigation
    del_res = await async_client.delete(f"/api/v1/investigations/{inv_id}")
    assert del_res.status_code == 200
    assert del_res.json() == {"deleted": True}

    # 5. Verify 404 after deletion
    get_again = await async_client.get(f"/api/v1/investigations/{inv_id}")
    assert get_again.status_code == 404
    err_body = get_again.json()
    assert err_body["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_investigation_validation_error(async_client: AsyncClient):
    # Empty targets must fail validation
    res = await async_client.post("/api/v1/investigations", json={})
    assert res.status_code == 422
    err_body = res.json()
    assert err_body["error"]["code"] == "VALIDATION_ERROR"
