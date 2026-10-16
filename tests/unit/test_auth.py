"""Unit tests for authentication, password hashing, JWT tokens, and account routes."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from opentrace.api.app import create_app
from opentrace.api.dependencies import get_storage, reset_dependencies
from opentrace.core.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from opentrace.storage.memory import MemoryStorage


def test_password_hashing() -> None:
    """Verify bcrypt hashing and validation."""
    pwd = "super-secret-password-123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_lifecycle() -> None:
    """Verify JWT token encoding, subject retrieval, and decoding."""
    token = create_access_token(subject="user-123", email="osint@example.com", role="user")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["email"] == "osint@example.com"
    assert payload["role"] == "user"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_auth_routes_end_to_end() -> None:
    """Test full registration, login, profile, and account deletion lifecycle."""
    reset_dependencies()
    storage = MemoryStorage()
    app = create_app()
    app.dependency_overrides[get_storage] = lambda: storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register new user
        reg_payload = {
            "email": "investigator@example.com",
            "password": "Password123!",
            "name": "OSINT Analyst",
        }
        res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_reg.status_code == 201
        data_reg = res_reg.json()
        assert "access_token" in data_reg
        token = data_reg["access_token"]
        user_id = data_reg["user"]["id"]
        assert data_reg["user"]["email"] == "investigator@example.com"
        assert data_reg["user"]["name"] == "OSINT Analyst"

        # 2. Duplicate registration should return 409 Conflict
        res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_dup.status_code == 409

        # 3. Login with credentials
        login_payload = {
            "email": "investigator@example.com",
            "password": "Password123!",
        }
        res_login = await client.post("/api/v1/auth/login", json=login_payload)
        assert res_login.status_code == 200
        data_login = res_login.json()
        assert data_login["access_token"] is not None

        # 4. Login with bad password returns 401
        res_bad = await client.post(
            "/api/v1/auth/login",
            json={"email": "investigator@example.com", "password": "wrong-password"},
        )
        assert res_bad.status_code == 401

        # 5. Access profile with token
        headers = {"Authorization": f"Bearer {token}"}
        res_me = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["id"] == user_id

        # 6. Update profile
        res_patch = await client.patch(
            "/api/v1/auth/me",
            headers=headers,
            json={"name": "Senior Investigator", "preferences": {"dark_mode": True}},
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["name"] == "Senior Investigator"
        assert res_patch.json()["preferences"]["dark_mode"] is True

        # 7. Change password
        res_pwd = await client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={"current_password": "Password123!", "new_password": "NewSecretPassword456!"},
        )
        assert res_pwd.status_code == 200

        # Login with old password fails
        res_old = await client.post("/api/v1/auth/login", json=login_payload)
        assert res_old.status_code == 401

        # Login with new password succeeds
        res_new = await client.post(
            "/api/v1/auth/login",
            json={"email": "investigator@example.com", "password": "NewSecretPassword456!"},
        )
        assert res_new.status_code == 200
        new_token = res_new.json()["access_token"]

        # 8. Password reset flow
        res_forgot = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "investigator@example.com"},
        )
        assert res_forgot.status_code == 200
        reset_token = res_forgot.json().get("reset_token")
        assert reset_token is not None

        res_reset = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": "FinalPassword789!"},
        )
        assert res_reset.status_code == 200

        # 9. Delete account
        del_headers = {"Authorization": f"Bearer {new_token}"}
        res_del = await client.delete("/api/v1/auth/me", headers=del_headers)
        assert res_del.status_code == 200
        assert res_del.json()["deleted"] is True

        # Profile access now fails
        res_gone = await client.get("/api/v1/auth/me", headers=del_headers)
        assert res_gone.status_code == 401
