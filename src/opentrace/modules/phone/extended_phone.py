"""Extended phone investigation modules: ITU-T E.164 compliance, Carrier prefix analysis, and Twilio/HLR provider lookup."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import phonenumbers
from phonenumbers import geocoder

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


class PhoneInternationalModule(OSINTModule):
    """Performs deep ITU-T E.164 numbering plan structure and international format validation."""

    metadata = ModuleMetadata(
        id="phone.international_format",
        name="ITU-T E.164 Format Validator",
        version="1.0.0",
        supported_targets=[TargetType.phone],
        source_name="ITU-T Numbering Authority",
        source_url="https://www.itu.int/net/itu-t/inr/nnp/",
        description="Validates international dialing structure, country code assignment, and ITU-T E.164 compliance.",
        category="phone",
        access_type="local_analysis",
        limitations=["Valid format confirms dialable allocation, not active subscriber connection"],
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
            "source_url": self.metadata.source_url,
            "limitations": self.metadata.limitations,
        }

        try:
            parsed = phonenumbers.parse(target, None)
            is_valid = phonenumbers.is_valid_number(parsed)
            is_possible = phonenumbers.is_possible_number(parsed)
            country_code = parsed.country_code
            national_num = str(parsed.national_number)
            intl_fmt = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            e164_fmt = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            rfc3966_fmt = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966)

            if is_valid:
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Compliant ITU-T E.164 number ({e164_fmt})",
                        "evidence": (
                            f"Phone number '{target}' is a fully compliant ITU-T E.164 number. "
                            f"Country Code: +{country_code}, National Number: {national_num}, "
                            f"Standard International: {intl_fmt}."
                        ),
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Validated against international telecommunications numbering plan"
                        ],
                        "data": {
                            "e164": e164_fmt,
                            "international": intl_fmt,
                            "rfc3966": rfc3966_fmt,
                            "country_code": country_code,
                            "national_number": national_num,
                            "is_valid": True,
                            "is_possible": True,
                        },
                        "evidence_hash": compute_evidence_hash("itut:e164", 200, e164_fmt),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Non-compliant ITU-T number format for '{target}'",
                        "evidence": f"Phone number '{target}' does not conform to an active ITU-T numbering plan.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Number failed ITU-T format and length checks"],
                        "data": {"is_valid": False, "is_possible": is_possible},
                        "evidence_hash": compute_evidence_hash("itut:e164", 400, "invalid"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Parsing failed for '{target}'",
                    "evidence": f"Error parsing phone number: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Parser exception"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash("itut:e164", 500, "parse_error"),
                }
            ]


class PhoneCarrierPrefixModule(OSINTModule):
    """Analyzes telecommunications national numbering prefixes and operating region allocation."""

    metadata = ModuleMetadata(
        id="phone.carrier_prefix",
        name="Telecommunications Carrier Prefix",
        version="1.0.0",
        supported_targets=[TargetType.phone],
        source_name="National Telecom Registry",
        source_url="https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country",
        description="Resolves national numbering prefixes to original telecom carrier networks and geographical zones.",
        category="phone",
        access_type="local_analysis",
        limitations=["Number porting (MNP) may allow transfer of number between carriers"],
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
            "source_url": self.metadata.source_url,
            "limitations": self.metadata.limitations,
        }

        try:
            parsed = phonenumbers.parse(target, None)
            if not phonenumbers.is_valid_number(parsed):
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No carrier prefix identified for '{target}'",
                        "evidence": "Phone number is not recognized as valid by national numbering authorities.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Invalid number format"],
                        "data": {},
                        "evidence_hash": compute_evidence_hash("telecom:prefix", 404, None),
                    }
                ]

            region_name = geocoder.description_for_number(parsed, "en") or "Unknown Region"
            from phonenumbers import carrier as carrier_mapper

            carrier_name = (
                carrier_mapper.name_for_number(parsed, "en") or "Unknown Telecom Provider"
            )

            return [
                {
                    **base,
                    "status": FindingStatus.found.value,
                    "source_status": SourceStatus.succeeded.value,
                    "verification_status": VerificationStatus.verified.value,
                    "title": f"Prefix allocated to {carrier_name} ({region_name})",
                    "evidence": (
                        f"Prefix for '{target}' belongs to carrier '{carrier_name}' in region '{region_name}'."
                    ),
                    "confidence": Confidence.medium.value,
                    "confidence_reasons": [
                        "Identified from official ITU and national carrier numbering plan prefix database"
                    ],
                    "data": {
                        "carrier": carrier_name,
                        "region": region_name,
                        "country_code": parsed.country_code,
                    },
                    "evidence_hash": compute_evidence_hash(
                        "telecom:prefix", 200, f"{carrier_name}:{region_name}"
                    ),
                }
            ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Error in carrier prefix lookup",
                    "evidence": f"Failed to map carrier prefix: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Lookup error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash("telecom:prefix", 500, "error"),
                }
            ]


class PhoneHlrLookupModule(OSINTModule):
    """Twilio / HLR Lookup authorized telecommunications live provider module."""

    metadata = ModuleMetadata(
        id="phone.hlr_lookup",
        name="Twilio Carrier Lookup (Authorized)",
        version="1.0.0",
        supported_targets=[TargetType.phone],
        source_name="Twilio Lookup API",
        source_url="https://www.twilio.com/docs/lookup/api",
        description="Authorized live carrier, MCC/MNC, and mobile line validation via official Twilio Lookup API.",
        category="phone",
        access_type="requires_api_key",
        limitations=[
            "Requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN. Reports skipped when unconfigured."
        ],
        timeout=8.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
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
            "source_url": "https://www.twilio.com/lookup",
            "limitations": self.metadata.limitations,
        }

        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.skipped.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Twilio Lookup API unconfigured (Skipped)",
                    "evidence": (
                        "TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN environment variables are not configured. "
                        "Live telecommunications provider query skipped."
                    ),
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Credentials unconfigured"],
                    "data": {"configured": False, "requires_api_key": True},
                    "evidence_hash": compute_evidence_hash(
                        base["source_url"], None, "unconfigured"
                    ),
                }
            ]

        # When configured, perform authorized lookup
        from urllib.parse import quote

        import httpx

        clean_num = target.strip()
        url = f"https://lookups.twilio.com/v1/PhoneNumbers/{quote(clean_num)}?Type=carrier"

        try:
            async with httpx.AsyncClient(
                timeout=8.0,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            ) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                carrier_info = data.get("carrier", {}) or {}
                name = carrier_info.get("name") or "Unknown"
                line_type = carrier_info.get("type") or "Unknown"
                mcc = carrier_info.get("mobile_country_code")
                mnc = carrier_info.get("mobile_network_code")

                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Twilio confirmed live carrier: {name} ({line_type})",
                        "evidence": f"Live telecommunications lookup confirmed carrier '{name}' (MCC: {mcc}, MNC: {mnc}, Type: {line_type}).",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Authorized real-time HLR network query via Twilio"],
                        "data": {
                            "carrier": name,
                            "line_type": line_type,
                            "mobile_country_code": mcc,
                            "mobile_network_code": mnc,
                            "configured": True,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"{name}:{mcc}:{mnc}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No Twilio record found for '{target}'",
                        "evidence": "Twilio Lookup API returned 404 for target phone number.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Twilio confirmed number not found"],
                        "data": {"configured": True},
                        "evidence_hash": compute_evidence_hash(url, 404, None),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Twilio API error HTTP {res.status_code}",
                        "evidence": "Remote Twilio API returned non-200 status code.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["API response code"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, None),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Error connecting to Twilio Lookup API",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]
