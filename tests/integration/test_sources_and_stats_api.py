"""Integration tests for sources catalog, stats endpoint, and investigation cancellation."""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from opentrace.api.app import create_app

client = TestClient(create_app())


def test_list_sources_endpoint() -> None:
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 50
    # Check structure
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "category" in first
    assert "target_type" in first
    assert "status" in first
    assert "is_active" in first


def test_filter_sources_endpoint() -> None:
    response = client.get("/api/v1/sources?status=implemented")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 20
    for s in data:
        assert s["status"] == "implemented"


def test_get_single_source_endpoint() -> None:
    response = client.get("/api/v1/sources/username.github")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "username.github"
    assert data["name"] == "GitHub"
    assert data["is_active"] is True


def test_get_nonexistent_source() -> None:
    response = client.get("/api/v1/sources/nonexistent.source.id")
    assert response.status_code == 404


def test_platform_stats_endpoint() -> None:
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_investigations" in data
    assert "total_manifest_sources" in data
    assert data["total_manifest_sources"] >= 50
    assert data["total_active_modules"] >= 20
    assert "sources_by_status" in data
    assert "sources_by_category" in data


@pytest.mark.asyncio
@respx.mock
async def test_investigation_with_name_target() -> None:
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=httpx.Response(
            200,
            json={
                "query": {
                    "search": [
                        {
                            "title": "Grace Hopper",
                            "pageid": 5678,
                            "snippet": "Grace Brewster Murray Hopper was an American computer scientist...",
                            "timestamp": "2023-01-01T00:00:00Z",
                        }
                    ]
                }
            },
        )
    )
    respx.get("https://dblp.org/search/author/api").mock(
        return_value=httpx.Response(200, json={"result": {"hits": {"@total": "0"}}})
    )
    respx.get("https://api.openalex.org/authors").mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    response = client.post("/api/v1/investigations", json={"name": "Grace Hopper"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("completed", "partial")
    assert "Grace Hopper" in data["request"]["name"]
    assert "metrics" in data["summary"]
    assert data["summary"]["metrics"]["attempted"] >= 1


def test_cancel_investigation_endpoint() -> None:
    # First create an investigation
    resp = client.post(
        "/api/v1/investigations", json={"username": "someuser", "modules": ["username.github"]}
    )
    assert resp.status_code == 200
    inv_id = resp.json()["id"]

    # Cancel endpoint
    cancel_resp = client.post(f"/api/v1/investigations/{inv_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["investigation_id"] == inv_id
