"""Gravatar public profile discovery module."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from opentrace.api.schemas.common import (
    Confidence,
    FindingStatus,
    SourceStatus,
    TargetType,
    VerificationStatus,
)
from opentrace.config import get_settings
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class GravatarEmailModule(OSINTModule):
    """Discovers public Gravatar profiles associated with an email hash."""

    _metadata = ModuleMetadata(
        id="email.gravatar",
        name="Gravatar Profile Discovery",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="Gravatar",
        source_url="https://en.gravatar.com/{hash}.json",
        description="Queries public Gravatar profile entries matching the MD5 email hash.",
        category="email",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Only retrieves profiles explicitly marked public by the owner."],
        timeout=5.0,
        max_requests=1,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)

        clean_email = target.strip().lower()
        email_hash = hashlib.md5(clean_email.encode("utf-8")).hexdigest()
        url = f"https://en.gravatar.com/{email_hash}.json"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": url,
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                entries = body.get("entry", [])
                if entries:
                    entry = entries[0]
                    display_name = entry.get("displayName") or entry.get("preferredUsername")
                    profile_url = entry.get("profileUrl")
                    about_me = entry.get("aboutMe")
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": display_name,
                            "profile_url": profile_url,
                            "title": f"Gravatar public profile found for '{target}'",
                            "evidence": f"Confirmed public Gravatar profile associated with email hash. Display name: '{display_name}'. Profile: {profile_url}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "HTTP 200 and verified public Gravatar entry returned"
                            ],
                            "data": {
                                "hash": email_hash,
                                "displayName": display_name,
                                "profileUrl": profile_url,
                                "aboutMe": about_me,
                            },
                            "evidence_hash": compute_evidence_hash(
                                url, 200, f"gravatar:{email_hash}"
                            ),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No Gravatar profile for '{target}'",
                            "evidence": "Gravatar returned empty entry list.",
                            "confidence": Confidence.medium.value,
                            "data": {"status_code": 200, "entries": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No Gravatar profile for '{target}'",
                        "evidence": f"Gravatar API returned 404 (no public profile exists for hash {email_hash}).",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Gravatar API"],
                        "data": {"status_code": 404, "hash": email_hash},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Gravatar check returned status {res.status_code}",
                        "evidence": f"HTTP {res.status_code} received from {url}.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "unknown"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "title": f"Gravatar check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
