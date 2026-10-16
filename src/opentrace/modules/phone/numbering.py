"""Phone numbering plan metadata module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import phonenumbers
from phonenumbers import carrier, geocoder

from opentrace.api.schemas.common import Confidence, FindingStatus, TargetType
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule

_NUMBER_TYPE_MAP = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    phonenumbers.PhoneNumberType.MOBILE: "MOBILE",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    phonenumbers.PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    phonenumbers.PhoneNumberType.SHARED_COST: "SHARED_COST",
    phonenumbers.PhoneNumberType.VOIP: "VOIP",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    phonenumbers.PhoneNumberType.PAGER: "PAGER",
    phonenumbers.PhoneNumberType.UAN: "UAN",
    phonenumbers.PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    phonenumbers.PhoneNumberType.UNKNOWN: "UNKNOWN",
}


class PhoneNumberingModule(OSINTModule):
    """Inspects phone numbering plan metadata according to ITU-T standards via libphonenumber."""

    _metadata = ModuleMetadata(
        id="phone.numbering",
        name="Phone Numbering Plan Metadata",
        version="0.1.0",
        supported_targets=[TargetType.phone],
        source_name="ITU-T Numbering Plan (libphonenumber)",
        source_url="https://github.com/google/libphonenumber",
        description="Analyzes phone numbers for format, country code, region, and line type.",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Provides numbering-plan metadata only.",
            "Does not establish subscriber identity, live network status, or current ported carrier.",
            "Geographic information denotes allocation region, not subscriber real-time location.",
        ],
        timeout=2.0,
        max_requests=0,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        finding_id = str(uuid.uuid4())

        base_finding: dict[str, Any] = {
            "id": finding_id,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "module_version": self.metadata.version,
            "target_type": TargetType.phone.value,
            "observed_at": observed_at,
            "source_name": self.metadata.source_name,
            "source_url": self.metadata.source_url,
        }

        try:
            parsed = phonenumbers.parse(target, None)
        except phonenumbers.NumberParseException as exc:
            ev_hash = compute_evidence_hash(
                self.metadata.source_url, None, f"parse_error:{str(exc)}"
            )
            return [
                {
                    **base_finding,
                    "status": FindingStatus.error.value,
                    "title": f"Invalid phone number format: '{target}'",
                    "evidence": f"Failed to parse phone number according to ITU-T standards: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"raw": target, "error": str(exc)},
                    "evidence_hash": ev_hash,
                }
            ]

        is_possible = phonenumbers.is_possible_number(parsed)
        is_valid = phonenumbers.is_valid_number(parsed)

        if not is_possible:
            ev_hash = compute_evidence_hash(
                self.metadata.source_url, None, f"impossible_number:{target}"
            )
            return [
                {
                    **base_finding,
                    "status": FindingStatus.error.value,
                    "title": f"Impossible phone number: '{target}'",
                    "evidence": "Number does not have a possible length or structure for any known numbering plan.",
                    "confidence": Confidence.none.value,
                    "data": {"raw": target, "is_possible": False, "is_valid": False},
                    "evidence_hash": ev_hash,
                }
            ]

        e164_format = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        international_format = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        national_format = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        )

        country_code = parsed.country_code
        region_code = phonenumbers.region_code_for_number(parsed)
        num_type_code = phonenumbers.number_type(parsed)
        num_type_str = _NUMBER_TYPE_MAP.get(num_type_code, "UNKNOWN")

        # Location and carrier descriptors (best effort)
        location_desc = geocoder.description_for_number(parsed, "en") or None
        carrier_name = carrier.name_for_number(parsed, "en") or None

        data = {
            "e164": e164_format,
            "international": international_format,
            "national": national_format,
            "country_calling_code": country_code,
            "region_code": region_code,
            "number_type": num_type_str,
            "is_valid": is_valid,
            "is_possible": is_possible,
            "location_description": location_desc,
            "original_carrier": carrier_name,
        }

        summary = f"phone_metadata:{e164_format}:{region_code}:{num_type_str}"
        ev_hash = compute_evidence_hash(self.metadata.source_url, 0, summary)

        status = FindingStatus.info.value if is_valid else FindingStatus.not_found.value
        confidence = Confidence.high.value if is_valid else Confidence.low.value

        evidence_parts = [
            f"E.164: {e164_format}",
            f"Region: {region_code or 'Unknown'}",
            f"Type: {num_type_str}",
            f"Valid ITU-T: {is_valid}",
        ]
        if location_desc:
            evidence_parts.append(f"Allocation area: {location_desc}")
        if carrier_name:
            evidence_parts.append(f"Assigned carrier (pre-porting): {carrier_name}")

        return [
            {
                **base_finding,
                "status": status,
                "title": f"Phone metadata for {e164_format} ({region_code or 'Unknown'})",
                "evidence": (
                    "Numbering plan details: "
                    + "; ".join(evidence_parts)
                    + ". Note: Does not identify subscriber, live status, or current SIM."
                ),
                "confidence": confidence,
                "data": data,
                "evidence_hash": ev_hash,
            }
        ]
