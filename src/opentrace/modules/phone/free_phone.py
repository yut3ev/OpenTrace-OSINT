"""Free phone metadata modules using phonenumbers and ITU-T standards without paid APIs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import phonenumbers
from phonenumbers import PhoneNumberType, timezone

from opentrace.api.schemas.common import (
    Confidence,
    FindingStatus,
    SourceStatus,
    TargetType,
    VerificationStatus,
)
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class PhoneTimezoneModule(OSINTModule):
    """Resolves geographic timezones and daylight-saving regions associated with the telephone numbering plan."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="phone.timezone",
            name="Phone Timezone & Geo-Region",
            version="1.0.0",
            supported_targets=[TargetType.phone],
            source_name="ITU-T / Phonenumbers Timezone Map",
            source_url="https://www.itu.int",
            description="Derives primary and regional timezones based on E.164 area code assignments.",
            category="phone",
            access_type="local_analysis",
            limitations=[
                "Timezone maps represent geographic allocation, not real-time physical GPS location."
            ],
            timeout=2.0,
            license="MIT",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.phone.value,
            "search_type": TargetType.phone.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": "https://www.itu.int/rec/T-REC-E.164",
            "limitations": self.metadata.limitations,
        }

        try:
            parsed = phonenumbers.parse(target, None)
            if not phonenumbers.is_possible_number(parsed):
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Impossible phone number structure for '{target}'",
                        "evidence": "Phone number could not be mapped to any known timezone.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["Number structure rejected by ITU-T tables"],
                        "data": {"raw": target},
                        "evidence_hash": compute_evidence_hash(target, None, "impossible"),
                    }
                ]

            tz_list = list(timezone.time_zones_for_number(parsed))
            primary_tz = tz_list[0] if tz_list else "Unknown"

            return [
                {
                    **base,
                    "status": FindingStatus.found.value,
                    "source_status": SourceStatus.succeeded.value,
                    "verification_status": VerificationStatus.verified.value,
                    "title": f"Timezone Mapped for '{target}': {primary_tz}",
                    "evidence": f"Mapped to {len(tz_list)} timezone(s): {', '.join(tz_list[:3])}.",
                    "confidence": Confidence.high.value,
                    "confidence_reasons": [
                        "E.164 national destination code mapped to IANA timezone database"
                    ],
                    "data": {
                        "primary_timezone": primary_tz,
                        "applicable_timezones": tz_list,
                        "country_code": parsed.country_code,
                    },
                    "evidence_hash": compute_evidence_hash(target, None, primary_tz),
                }
            ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Timezone resolution error for '{target}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Parsing error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(target, None, "error"),
                }
            ]


class PhoneValidationRulesModule(OSINTModule):
    """Performs deep ITU-T E.164 rule checks, line classification, and length sanity audits."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="phone.validation_rules",
            name="ITU-T Number Type & Line Validation",
            version="1.0.0",
            supported_targets=[TargetType.phone],
            source_name="ITU-T Standards Validation",
            source_url="https://www.itu.int",
            description="Evaluates phone number type classification (mobile, fixed-line, toll-free, premium).",
            category="phone",
            access_type="local_analysis",
            limitations=["Determines line category allocation, not active subscription status."],
            timeout=2.0,
            license="MIT",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.phone.value,
            "search_type": TargetType.phone.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": "https://www.itu.int",
            "limitations": self.metadata.limitations,
        }

        try:
            parsed = phonenumbers.parse(target, None)
            is_valid = phonenumbers.is_valid_number(parsed)
            num_type_code = phonenumbers.number_type(parsed)

            type_map = {
                PhoneNumberType.FIXED_LINE: "fixed_line",
                PhoneNumberType.MOBILE: "mobile",
                PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
                PhoneNumberType.TOLL_FREE: "toll_free",
                PhoneNumberType.PREMIUM_RATE: "premium_rate",
                PhoneNumberType.SHARED_COST: "shared_cost",
                PhoneNumberType.VOIP: "voip",
                PhoneNumberType.PERSONAL_NUMBER: "personal_number",
                PhoneNumberType.PAGER: "pager",
                PhoneNumberType.UAN: "uan",
                PhoneNumberType.VOICEMAIL: "voicemail",
                PhoneNumberType.UNKNOWN: "unknown",
            }
            line_type = type_map.get(num_type_code, "unknown")

            if is_valid:
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Valid {line_type.replace('_', ' ').title()} Phone Number ({target})",
                        "evidence": f"Confirmed valid E.164 numbering structure classified as '{line_type}'.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Passed full ITU-T E.164 national numbering plan validation"
                        ],
                        "data": {
                            "is_valid": True,
                            "line_type": line_type,
                            "country_code": parsed.country_code,
                            "national_number": parsed.national_number,
                        },
                        "evidence_hash": compute_evidence_hash(target, None, line_type),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Invalid numbering structure for '{target}'",
                        "evidence": "Number does not conform to national numbering plan rules.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Failed ITU-T national numbering plan validation rules"
                        ],
                        "data": {"is_valid": False, "line_type": line_type},
                        "evidence_hash": compute_evidence_hash(target, None, "invalid"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Validation rule error for '{target}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Parsing error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(target, None, "error"),
                }
            ]
