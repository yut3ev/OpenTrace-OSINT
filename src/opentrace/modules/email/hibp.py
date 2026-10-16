"""Authorized HaveIBeenPwned email breach discovery module."""

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


class HaveIBeenPwnedEmailModule(OSINTModule):
    """Queries official HaveIBeenPwned API for public breach appearances when authorized."""

    _metadata = ModuleMetadata(
        id="email.hibp",
        name="HaveIBeenPwned API (Authorized)",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="HaveIBeenPwned",
        source_url="https://haveibeenpwned.com/account/{email}",
        description="Queries official HaveIBeenPwned API for authorized breach incident metadata.",
        category="email",
        access_type="requires_api_key",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Requires official HIBP_API_KEY. Reports requires_api_key when unconfigured.",
            "Indicates presence in public disclosures, not password compromise.",
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
            "source_url": f"https://haveibeenpwned.com/account/{target}",
            "limitations": self.metadata.limitations,
        }

        # Check if API key is configured
        api_key = settings.hibp_api_key
        if not api_key:
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.skipped.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"HaveIBeenPwned lookup skipped for '{target}' (API key not configured)",
                    "evidence": (
                        "HIBP_API_KEY environment variable is not configured. "
                        "Authorized lookup requires an active subscription key from haveibeenpwned.com/API/v3."
                    ),
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["HIBP_API_KEY not present in environment"],
                    "data": {"configured": False, "requires_api_key": True},
                    "evidence_hash": compute_evidence_hash(
                        base["source_url"], None, "unconfigured"
                    ),
                }
            ]

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{target}?truncateResponse=false"
        headers = {
            "hibp-api-key": api_key,
            "user-agent": settings.user_agent,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=4.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                breaches = res.json()
                breach_names = [b.get("Name", "Unknown") for b in breaches if isinstance(b, dict)]
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Found in {len(breaches)} public breach disclosures on HaveIBeenPwned",
                        "evidence": f"Address '{target}' indexed in public breach records: {', '.join(breach_names[:10])}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Direct match from official HaveIBeenPwned API"],
                        "data": {
                            "configured": True,
                            "breach_count": len(breaches),
                            "breaches": breach_names,
                        },
                        "evidence_hash": compute_evidence_hash(
                            url, 200, f"breaches:{len(breaches)}"
                        ),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"No breach appearances found for '{target}' on HaveIBeenPwned",
                        "evidence": f"HaveIBeenPwned API returned HTTP 404 Not Found for '{target}'.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Official API confirmed no record of breached account"
                        ],
                        "data": {"configured": True, "breach_count": 0},
                        "evidence_hash": compute_evidence_hash(url, 404, "clean"),
                    }
                ]
            elif res.status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": "HaveIBeenPwned API rate limit exceeded",
                        "evidence": "Received HTTP 429 Too Many Requests from HaveIBeenPwned API.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": 429},
                        "evidence_hash": compute_evidence_hash(url, 429, "rate_limited"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.blocked.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"HaveIBeenPwned API returned status {res.status_code}",
                        "evidence": f"Unexpected response code {res.status_code} from HIBP API.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "api_error"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"HaveIBeenPwned check error for '{target}'",
                    "evidence": f"Network error communicating with HIBP API: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
