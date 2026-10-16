"""Authorized phone carrier and provider lookup module."""

from __future__ import annotations

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
from opentrace.config import Settings, get_settings
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class AuthorizedPhoneLookupModule(OSINTModule):
    """Queries authorized phone provider APIs (Numverify / Carrier lookup) when credentials exist."""

    _metadata = ModuleMetadata(
        id="phone.provider_api",
        name="Authorized Phone Lookup Provider",
        version="0.1.0",
        supported_targets=[TargetType.phone],
        source_name="Numverify Provider API",
        source_url="https://numverify.com",
        description="Queries authorized Numverify API for real-time carrier, line type, and location.",
        category="phone",
        access_type="requires_api_key",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Requires NUMVERIFY_API_KEY environment variable. Reports requires_api_key when unconfigured.",
            "Validates line allocation and carrier assignment, not active subscriber identity.",
        ],
        timeout=8.0,
        max_requests=1,
    )

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    @property
    def settings(self) -> Settings:
        return self._settings or get_settings()

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = self.settings
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        clean_num = target.lstrip("+").strip()

        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.phone.value,
            "search_type": TargetType.phone.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": "https://numverify.com",
            "limitations": self.metadata.limitations,
        }

        api_key = settings.numverify_api_key
        if not api_key:
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.skipped.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Phone provider lookup skipped for '{target}' (API key not configured)",
                    "evidence": (
                        "NUMVERIFY_API_KEY environment variable is not configured. "
                        "Authorized carrier lookup requires an active API key from numverify.com."
                    ),
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["NUMVERIFY_API_KEY not configured in environment"],
                    "data": {"configured": False, "requires_api_key": True},
                    "evidence_hash": compute_evidence_hash(
                        base["source_url"], None, "unconfigured"
                    ),
                }
            ]

        url = f"https://apilayer.net/api/validate?access_key={api_key}&number={clean_num}&country_code=&format=1"

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=4.0)
            ) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                is_valid = data.get("valid", False)
                carrier = data.get("carrier") or "Unknown Carrier"
                line_type = data.get("line_type") or "Unknown"
                country = data.get("country_name") or "Unknown"
                location = data.get("location") or country

                if is_valid:
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Provider confirmed {line_type} line ({carrier}, {location})",
                            "evidence": (
                                f"Numverify verified phone number '{target}'. Carrier: {carrier}, "
                                f"Line type: {line_type}, Location: {location}."
                            ),
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Numverify real-time telecommunications carrier validation"
                            ],
                            "data": {
                                "configured": True,
                                "valid": True,
                                "carrier": carrier,
                                "line_type": line_type,
                                "country": country,
                                "location": location,
                            },
                            "evidence_hash": compute_evidence_hash(
                                "numverify", 200, f"{clean_num}:{carrier}:{line_type}"
                            ),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Phone number '{target}' reported invalid by provider",
                            "evidence": f"Numverify API reported that '{target}' is not an allocated or active numbering block.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["Provider confirmed non-allocated number"],
                            "data": {"configured": True, "valid": False},
                            "evidence_hash": compute_evidence_hash(
                                "numverify", 200, f"{clean_num}:invalid"
                            ),
                        }
                    ]
            elif res.status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": "Numverify provider rate limit exceeded",
                        "evidence": "Received HTTP 429 Too Many Requests from Numverify API.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": 429},
                        "evidence_hash": compute_evidence_hash("numverify", 429, "rate_limited"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.blocked.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Numverify returned status {res.status_code}",
                        "evidence": f"Unexpected HTTP status {res.status_code} from provider API.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(
                            "numverify", res.status_code, "api_error"
                        ),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Phone provider check failed for '{target}'",
                    "evidence": f"Network error connecting to phone provider API: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash("numverify", None, f"error:{exc}"),
                }
            ]
