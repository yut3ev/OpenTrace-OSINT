"""GitLab public profile checking module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from opentrace.api.schemas.common import Confidence, FindingStatus, TargetType
from opentrace.config import get_settings
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class GitLabUsernameModule(OSINTModule):
    """Checks public GitLab profiles using the GitLab REST API."""

    _metadata = ModuleMetadata(
        id="username.gitlab",
        name="GitLab Public Profile",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="GitLab",
        source_url="https://gitlab.com/api/v4/users?username={username}",
        description="Queries public GitLab user profiles via the public REST API.",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Rate limits apply per IP address.",
            "Profile existence does not confirm real identity or ownership.",
        ],
        timeout=10.0,
        max_requests=1,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://gitlab.com/api/v4/users?username={target}"
        headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/json",
        }

        finding_id = str(uuid.uuid4())
        base_finding: dict[str, Any] = {
            "id": finding_id,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "module_version": self.metadata.version,
            "target_type": TargetType.username.value,
            "observed_at": observed_at,
            "source_name": self.metadata.source_name,
            "source_url": f"https://gitlab.com/{target}",
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                response = await client.get(url, headers=headers)

            status_code = response.status_code
            if status_code == 200:
                body = response.json()
                if isinstance(body, list) and len(body) > 0:
                    user_data = body[0]
                    profile_url = user_data.get("web_url", f"https://gitlab.com/{target}")
                    public_data = {
                        "id": user_data.get("id"),
                        "username": user_data.get("username"),
                        "name": user_data.get("name"),
                        "state": user_data.get("state"),
                        "profile_url": profile_url,
                    }
                    summary = f"GitLab profile exists for '{target}'"
                    ev_hash = compute_evidence_hash(profile_url, status_code, summary)
                    return [
                        {
                            **base_finding,
                            "status": FindingStatus.found.value,
                            "title": f"GitLab user '{target}' found",
                            "evidence": f"Public profile returned HTTP 200 at {url}.",
                            "confidence": Confidence.medium.value,
                            "source_url": profile_url,
                            "data": public_data,
                            "evidence_hash": ev_hash,
                        }
                    ]
                else:
                    summary = f"GitLab user '{target}' not found"
                    ev_hash = compute_evidence_hash(url, status_code, summary)
                    return [
                        {
                            **base_finding,
                            "status": FindingStatus.not_found.value,
                            "title": f"GitLab user '{target}' not found",
                            "evidence": f"API returned empty result for username '{target}'.",
                            "confidence": Confidence.medium.value,
                            "data": {"status_code": 200, "result_count": 0},
                            "evidence_hash": ev_hash,
                        }
                    ]
            elif status_code == 404:
                summary = f"GitLab user '{target}' not found (404)"
                ev_hash = compute_evidence_hash(url, status_code, summary)
                return [
                    {
                        **base_finding,
                        "status": FindingStatus.not_found.value,
                        "title": f"GitLab user '{target}' not found",
                        "evidence": f"API returned HTTP 404 at {url}.",
                        "confidence": Confidence.medium.value,
                        "data": {"status_code": 404},
                        "evidence_hash": ev_hash,
                    }
                ]
            elif status_code in (401, 403, 429):
                evidence_text = (
                    "Rate limited or access restricted"
                    if status_code in (403, 429)
                    else "Unauthorized"
                )
                summary = f"GitLab API check restricted ({status_code})"
                ev_hash = compute_evidence_hash(url, status_code, summary)
                return [
                    {
                        **base_finding,
                        "status": FindingStatus.unknown.value,
                        "title": f"GitLab check restricted for '{target}'",
                        "evidence": f"{evidence_text} (HTTP {status_code}). Result is unknown.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": status_code},
                        "evidence_hash": ev_hash,
                    }
                ]
            else:
                summary = f"GitLab unexpected status {status_code}"
                ev_hash = compute_evidence_hash(url, status_code, summary)
                return [
                    {
                        **base_finding,
                        "status": FindingStatus.unknown.value,
                        "title": f"GitLab check returned unexpected status {status_code}",
                        "evidence": f"HTTP {status_code} received from {url}.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": status_code},
                        "evidence_hash": ev_hash,
                    }
                ]

        except httpx.TimeoutException:
            ev_hash = compute_evidence_hash(url, None, "timeout")
            return [
                {
                    **base_finding,
                    "status": FindingStatus.unknown.value,
                    "title": f"GitLab check timed out for '{target}'",
                    "evidence": f"Connection timed out after {self.metadata.timeout}s.",
                    "confidence": Confidence.none.value,
                    "data": {"error": "timeout"},
                    "evidence_hash": ev_hash,
                }
            ]
        except Exception as exc:
            ev_hash = compute_evidence_hash(url, None, f"error: {str(exc)}")
            return [
                {
                    **base_finding,
                    "status": FindingStatus.unknown.value,
                    "title": f"GitLab check failed for '{target}'",
                    "evidence": f"Network or client error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": ev_hash,
                }
            ]
