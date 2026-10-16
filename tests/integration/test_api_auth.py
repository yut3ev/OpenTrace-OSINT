"""Integration tests for API key authentication and security headers."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

import opentrace.config as config_module
from opentrace.api.app import create_app


@pytest.mark.asyncio
async def test_api_key_auth_enforced_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """When OPENTRACE_API_KEY is configured, protected endpoints must return 401 without valid key."""
    monkeypatch.setenv("OPENTRACE_API_KEY", "super-secret-token-789")
    config_module.reset_settings()

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Public health check should always succeed without auth
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200

        # Protected endpoint without auth -> 401
        unauth_resp = await client.get("/api/v1/modules")
        assert unauth_resp.status_code == 401
        assert "Unauthorized" in unauth_resp.json()["error"]

        # Protected endpoint with invalid X-API-Key -> 401
        bad_key_resp = await client.get("/api/v1/modules", headers={"X-API-Key": "wrong-key"})
        assert bad_key_resp.status_code == 401

        # Protected endpoint with valid X-API-Key -> 200
        valid_x_resp = await client.get(
            "/api/v1/modules", headers={"X-API-Key": "super-secret-token-789"}
        )
        assert valid_x_resp.status_code == 200

        # Protected endpoint with valid Authorization Bearer -> 200
        valid_bearer_resp = await client.get(
            "/api/v1/modules", headers={"Authorization": "Bearer super-secret-token-789"}
        )
        assert valid_bearer_resp.status_code == 200

    # Clean up settings singleton
    config_module.reset_settings()
