"""Base definitions and interfaces for OSINT modules and source adapters."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from opentrace.api.schemas.common import TargetType


@dataclass
class ModuleMetadata:
    """Metadata describing an OSINT module's identity, capabilities, and operational limits."""

    id: str
    name: str
    version: str
    supported_targets: list[TargetType]
    source_name: str
    source_url: str
    description: str
    enabled: bool = True
    implementation_status: str = "implemented"  # implemented, tested, requires_api_key, requires_oauth, public_web, temporarily_unavailable, planned
    category: str = "general"  # developer, social, blogging, creative, gaming, messaging, email, phone, people, web
    access_type: str = "public_web"  # public_web, public_api, requires_api_key, local_analysis
    limitations: list[str] = field(default_factory=list)
    timeout: float = 10.0
    max_requests: int = 5
    rate_limit_per_second: float = 1.0
    license: str = "MIT"
    requires_api_key: bool = False
    is_free: bool = True
    rate_limit_policy: str = "default"


class OSINTModule(abc.ABC):
    """Abstract base class for all OSINT collection modules and source adapters."""

    @property
    @abc.abstractmethod
    def metadata(self) -> ModuleMetadata:
        """Module metadata declaration."""
        ...

    @abc.abstractmethod
    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute the module against a normalized target identifier.

        Returns a list of raw finding dictionaries conforming to FindingSchema.
        """
        ...

    @property
    def source_id(self) -> str:
        return self.metadata.id

    @property
    def source_name(self) -> str:
        return self.metadata.source_name

    @property
    def category(self) -> str:
        return self.metadata.category

    @property
    def base_url(self) -> str:
        return self.metadata.source_url

    @property
    def license(self) -> str:
        return self.metadata.license

    @property
    def requires_api_key(self) -> bool:
        return self.metadata.requires_api_key

    @property
    def is_free(self) -> bool:
        return self.metadata.is_free

    @property
    def timeout(self) -> float:
        return self.metadata.timeout

    @property
    def rate_limit_policy(self) -> str:
        return self.metadata.rate_limit_policy

    async def check_availability(self) -> bool:
        """Check if source is reachable and operational."""
        return self.metadata.enabled

    async def health_check(self) -> dict[str, Any]:
        """Perform a basic health check on the source adapter."""
        return {
            "source_id": self.source_id,
            "status": "healthy" if self.metadata.enabled else "disabled",
            "is_free": self.is_free,
            "requires_api_key": self.requires_api_key,
        }

    async def search(
        self, query: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Unified search interface delegating to run()."""
        return await self.run(query, context)

    def normalize_result(self, raw_result: dict[str, Any]) -> dict[str, Any]:
        """Normalize raw finding dictionary according to common schema."""
        return raw_result

    def supports(self, target_type: TargetType | str) -> bool:
        """Check if target type is supported by this module."""
        val = target_type.value if isinstance(target_type, TargetType) else target_type
        return any(t.value == val for t in self.metadata.supported_targets)


class BaseUsernameAdapter(OSINTModule):
    """High-reliability base adapter for public username profile discovery.

    Handles URL templating, soft-404 detection, JSON/HTML validation, rate-limiting,
    honest status taxonomy, and cryptographic evidence hashing.
    """

    url_pattern: str = ""
    profile_url_pattern: str = ""
    soft_404_indicators: list[str] = []
    positive_indicators: list[str] = []
    json_required_keys: list[str] = []
    custom_headers: dict[str, str] = {}
    is_json_api: bool = False

    def get_url(self, username: str) -> str:
        return self.url_pattern.format(username=username)

    def get_profile_url(self, username: str) -> str:
        pattern = self.profile_url_pattern or self.url_pattern
        return pattern.format(username=username)

    def extract_profile_data(
        self,
        response: Any,
        username: str,  # response is httpx.Response
    ) -> dict[str, Any]:
        """Override to extract structured fields like display_name, avatar_url, bio, etc."""
        if self.is_json_api:
            try:
                data = response.json()
                if isinstance(data, dict):
                    return {
                        "username": username,
                        "profile_url": self.get_profile_url(username),
                        "display_name": data.get("name") or data.get("display_name") or username,
                        "bio": data.get("bio") or data.get("description"),
                        "avatar_url": data.get("avatar_url") or data.get("avatar"),
                    }
            except Exception:
                pass
        return {
            "username": username,
            "profile_url": self.get_profile_url(username),
        }

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        import uuid
        from datetime import UTC, datetime

        import httpx

        from opentrace.api.schemas.common import (
            Confidence,
            FindingStatus,
            SourceStatus,
            VerificationStatus,
        )
        from opentrace.config import get_settings
        from opentrace.core.evidence import compute_evidence_hash

        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = self.get_url(target)
        profile_url = self.get_profile_url(target)

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": profile_url,
            "limitations": self.metadata.limitations,
        }

        headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/json"
            if self.is_json_api
            else "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            **self.custom_headers,
        }

        timeout = httpx.Timeout(self.metadata.timeout, connect=4.0)

        try:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True, headers=headers
            ) as client:
                res = await client.get(url)

            status_code = res.status_code
            body_text = res.text

            # 1. Successful HTTP 200 response
            if status_code == 200:
                # Check for soft-404 text indicators
                lower_body = body_text.lower()
                for indicator in self.soft_404_indicators:
                    if indicator.lower() in lower_body:
                        return [
                            {
                                **base,
                                "status": FindingStatus.not_found.value,
                                "source_status": SourceStatus.no_match.value,
                                "verification_status": VerificationStatus.unverified.value,
                                "title": f"No public profile for '{target}' on {self.metadata.source_name}",
                                "evidence": f"Soft-404 detected: page contains '{indicator}'.",
                                "confidence": Confidence.high.value,
                                "confidence_reasons": [
                                    "Soft-404 text pattern matched on source response"
                                ],
                                "data": {"status_code": 200, "soft_404": True},
                                "evidence_hash": compute_evidence_hash(url, 200, indicator),
                            }
                        ]

                # Check JSON required keys if applicable
                if self.is_json_api:
                    try:
                        json_data = res.json()
                        if isinstance(json_data, dict):
                            for req_key in self.json_required_keys:
                                if req_key not in json_data:
                                    return [
                                        {
                                            **base,
                                            "status": FindingStatus.not_found.value,
                                            "source_status": SourceStatus.no_match.value,
                                            "verification_status": VerificationStatus.unverified.value,
                                            "title": f"No public profile for '{target}' on {self.metadata.source_name}",
                                            "evidence": f"JSON payload missing expected key '{req_key}'.",
                                            "confidence": Confidence.medium.value,
                                            "confidence_reasons": [
                                                "API response missing required user identity fields"
                                            ],
                                            "data": {"status_code": 200},
                                            "evidence_hash": compute_evidence_hash(
                                                url, 200, "missing_key"
                                            ),
                                        }
                                    ]
                    except Exception:
                        return [
                            {
                                **base,
                                "status": FindingStatus.unknown.value,
                                "source_status": SourceStatus.unavailable.value,
                                "verification_status": VerificationStatus.unverified.value,
                                "title": f"Invalid JSON response from {self.metadata.source_name}",
                                "evidence": "Failed to parse API response as JSON.",
                                "confidence": Confidence.none.value,
                                "confidence_reasons": ["JSON parse error from remote endpoint"],
                                "data": {"status_code": 200},
                                "evidence_hash": compute_evidence_hash(url, 200, "json_error"),
                            }
                        ]

                # Confirmed valid profile
                extracted = self.extract_profile_data(res, target)
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Public profile found for '{target}' on {self.metadata.source_name}",
                        "evidence": f"Confirmed public profile at {profile_url} (HTTP 200).",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            f"Verified public profile on {self.metadata.source_name} without error or redirect markers"
                        ],
                        "data": extracted,
                        "evidence_hash": compute_evidence_hash(
                            url, 200, body_text[:200] if body_text else target
                        ),
                    }
                ]

            # 2. Definite 404 Not Found
            elif status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No profile found for '{target}' on {self.metadata.source_name}",
                        "evidence": f"{self.metadata.source_name} returned HTTP 404 Not Found.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["HTTP 404 verified non-existence of public profile"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, None),
                    }
                ]

            # 3. Rate Limited
            elif status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Rate limit reached on {self.metadata.source_name}",
                        "evidence": f"HTTP 429 Too Many Requests from {self.metadata.source_name}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Source throttled request due to rate limits"],
                        "data": {"status_code": 429},
                        "evidence_hash": compute_evidence_hash(url, 429, None),
                    }
                ]

            # 4. Access Blocked / WAF / Cloudflare
            elif status_code in (401, 403):
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.blocked.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Access blocked by {self.metadata.source_name}",
                        "evidence": f"HTTP {status_code} Access Denied / WAF challenge.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Remote host rejected unauthenticated request"],
                        "data": {"status_code": status_code},
                        "evidence_hash": compute_evidence_hash(url, status_code, None),
                    }
                ]

            # 5. Server Error
            elif status_code >= 500:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Service unavailable for {self.metadata.source_name}",
                        "evidence": f"Remote server returned HTTP {status_code} server error.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Remote service outage or internal server error"],
                        "data": {"status_code": status_code},
                        "evidence_hash": compute_evidence_hash(url, status_code, None),
                    }
                ]

            # Other status codes
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Unexpected response from {self.metadata.source_name}",
                        "evidence": f"Remote host returned unexpected HTTP status {status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Non-standard HTTP status code"],
                        "data": {"status_code": status_code},
                        "evidence_hash": compute_evidence_hash(url, status_code, None),
                    }
                ]

        except TimeoutError:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.unavailable.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Timeout connecting to {self.metadata.source_name}",
                    "evidence": f"Request exceeded timeout limit of {self.metadata.timeout}s.",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network timeout"],
                    "data": {"timeout": True},
                    "evidence_hash": compute_evidence_hash(url, None, "timeout"),
                }
            ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Connection error for {self.metadata.source_name}",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]
