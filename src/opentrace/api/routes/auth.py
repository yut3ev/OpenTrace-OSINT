"""Authentication and account management endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from opentrace.api.dependencies import get_app_settings, get_current_user, get_storage
from opentrace.api.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from opentrace.config import Settings
from opentrace.core.auth import (
    auth_rate_limiter,
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_token,
    verify_password,
)
from opentrace.storage.interface import StorageBackend

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    payload: UserRegisterRequest,
    storage: Annotated[StorageBackend, Depends(get_storage)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TokenResponse:
    """Register a new user account."""
    client_ip = request.client.host if request.client else "unknown"
    if not auth_rate_limiter.is_allowed(f"register:{client_ip}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is currently disabled.",
        )

    email = payload.email.strip().lower()
    existing = await storage.get_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    now_str = datetime.now(UTC).isoformat()
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(payload.password)

    role = "admin" if (settings.admin_email and email == settings.admin_email.lower()) else "user"

    user_dict: dict[str, Any] = {
        "id": user_id,
        "email": email,
        "hashed_password": hashed_pwd,
        "name": payload.name.strip(),
        "role": role,
        "is_active": True,
        "preferences": {},
        "created_at": now_str,
        "updated_at": now_str,
    }

    created = await storage.create_user(user_dict)
    await storage.create_audit_event(
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": "user.registered",
            "ip_address": client_ip,
            "created_at": now_str,
            "details": {"email": email},
        }
    )

    token = create_access_token(subject=user_id, email=email, role=role)
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        user=UserResponse.model_validate(created),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: UserLoginRequest,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> TokenResponse:
    """Authenticate with email and password and receive a JWT token."""
    client_ip = request.client.host if request.client else "unknown"
    email = payload.email.strip().lower()

    if not auth_rate_limiter.is_allowed(f"login:{client_ip}:{email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait a minute and try again.",
        )

    user = await storage.get_user_by_email(email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    token = create_access_token(
        subject=user["id"],
        email=user["email"],
        role=user.get("role", "user"),
    )

    await storage.create_audit_event(
        {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "action": "user.login",
            "ip_address": client_ip,
            "created_at": datetime.now(UTC).isoformat(),
            "details": {},
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, bool]:
    """Log out the current session."""
    await storage.create_audit_event(
        {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "action": "user.logout",
            "ip_address": None,
            "created_at": datetime.now(UTC).isoformat(),
            "details": {},
        }
    )
    return {"logged_out": True}


@router.get("/me", response_model=UserResponse)
async def get_profile(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> UserResponse:
    """Retrieve current authenticated user profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    payload: UserUpdateRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> UserResponse:
    """Update profile details or user preferences."""
    updates: dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.preferences is not None:
        current_prefs = current_user.get("preferences", {})
        current_prefs.update(payload.preferences)
        updates["preferences"] = current_prefs

    if updates:
        updated = await storage.update_user(current_user["id"], updates)
        if updated:
            return UserResponse.model_validate(updated)

    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, str]:
    """Change user password after verifying current password."""
    if not verify_password(payload.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    new_hash = hash_password(payload.new_password)
    await storage.update_user(current_user["id"], {"hashed_password": new_hash})
    await storage.create_audit_event(
        {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            "action": "user.password_changed",
            "ip_address": None,
            "created_at": datetime.now(UTC).isoformat(),
            "details": {},
        }
    )
    return {"message": "Password changed successfully."}


@router.delete("/me")
async def delete_account(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, bool]:
    """Permanently delete user account and associated investigation records."""
    deleted = await storage.delete_user(current_user["id"])
    return {"deleted": deleted}


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, Any]:
    """Request a password reset token."""
    email = payload.email.strip().lower()
    user = await storage.get_user_by_email(email)
    token = None
    if user:
        token = generate_reset_token()
        t_hash = hash_token(token)
        expires_at = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        await storage.create_password_reset(
            {
                "token_hash": t_hash,
                "user_id": user["id"],
                "expires_at": expires_at,
                "used": False,
            }
        )

    # Return standard response to prevent user enumeration, but include token for self-hosted/demo usage
    resp: dict[str, Any] = {
        "message": "If your email is registered, a password reset link/token has been generated."
    }
    if token:
        resp["reset_token"] = token
    return resp


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> dict[str, str]:
    """Reset password using a valid reset token."""
    t_hash = hash_token(payload.token.strip())
    reset_record = await storage.get_password_reset(t_hash)
    if not reset_record or reset_record.get("used"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    expires_at = datetime.fromisoformat(reset_record["expires_at"])
    if datetime.now(UTC) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired.",
        )

    new_hash = hash_password(payload.new_password)
    await storage.update_user(reset_record["user_id"], {"hashed_password": new_hash})
    await storage.mark_password_reset_used(t_hash)

    await storage.create_audit_event(
        {
            "id": str(uuid.uuid4()),
            "user_id": reset_record["user_id"],
            "action": "user.password_reset_completed",
            "ip_address": None,
            "created_at": datetime.now(UTC).isoformat(),
            "details": {},
        }
    )
    return {"message": "Password has been reset successfully. You can now log in."}
