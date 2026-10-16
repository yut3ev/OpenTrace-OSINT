"""Free public email and domain OSINT modules without paid APIs."""

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
from opentrace.config import get_settings
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class EmailRDAPDomainModule(OSINTModule):
    """Queries official ICANN RDAP (Registration Data Access Protocol) for domain registration metadata."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="email.rdap_domain",
            name="Domain RDAP Registration Info",
            version="1.0.0",
            supported_targets=[TargetType.email],
            source_name="ICANN / RIPE RDAP Gateway",
            source_url="https://rdap.org",
            description="Queries open RDAP gateways for domain registrar, creation date, and status.",
            category="email",
            access_type="public_api",
            limitations=["Returns domain registry metadata, not individual mailbox ownership."],
            timeout=8.0,
            license="MIT",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        domain = target.split("@")[-1].strip().lower() if "@" in target else target.strip().lower()
        url = f"https://rdap.org/domain/{domain}"

        base: dict[str, Any] = {
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
                timeout=httpx.Timeout(self.metadata.timeout, connect=4.0),
                headers={
                    "User-Agent": settings.user_agent,
                    "Accept": "application/rdap+json,application/json",
                },
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)

            if resp.status_code == 200:
                data = resp.json()
                handle = data.get("handle", "")
                events = data.get("events", [])
                created_date = next(
                    (e.get("eventDate") for e in events if e.get("eventAction") == "registration"),
                    None,
                )
                last_changed = next(
                    (e.get("eventDate") for e in events if e.get("eventAction") == "last changed"),
                    None,
                )
                status_list = data.get("status", [])

                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Domain RDAP Record Found for '{domain}'",
                        "evidence": f"Registered domain under handle {handle or domain}. Created: {created_date or 'Unknown'}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Official RDAP registration metadata resolved"],
                        "data": {
                            "domain": domain,
                            "handle": handle,
                            "registration_date": created_date,
                            "last_changed": last_changed,
                            "domain_status": status_list,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, handle or domain),
                    }
                ]
            elif resp.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No RDAP record found for '{domain}'",
                        "evidence": "RDAP server returned HTTP 404 Not Found.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["Domain not found in RDAP registry"],
                        "data": {"domain": domain},
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
                        "title": f"RDAP lookup failed for '{domain}'",
                        "evidence": f"RDAP gateway returned HTTP {resp.status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": [f"HTTP {resp.status_code}"],
                        "data": {"status_code": resp.status_code},
                        "evidence_hash": compute_evidence_hash(url, resp.status_code, None),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Connection error during RDAP lookup for '{domain}'",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class EmailSecurityTxtModule(OSINTModule):
    """Checks for RFC 9116 security.txt policy and vulnerability disclosure contacts."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="email.security_txt",
            name="RFC 9116 security.txt Policy",
            version="1.0.0",
            supported_targets=[TargetType.email],
            source_name="RFC 9116 security.txt",
            source_url="https://www.rfc-editor.org/rfc/rfc9116",
            description="Checks domain for standard security.txt vulnerability disclosure contacts.",
            category="email",
            access_type="public_web",
            limitations=["Applies to domain security policies; does not inspect email mailboxes."],
            timeout=6.0,
            license="MIT",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        domain = target.split("@")[-1].strip().lower() if "@" in target else target.strip().lower()
        url = f"https://{domain}/.well-known/security.txt"

        base: dict[str, Any] = {
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
                timeout=httpx.Timeout(self.metadata.timeout, connect=3.0),
                headers={"User-Agent": settings.user_agent},
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)

            if resp.status_code == 200 and "contact:" in resp.text.lower():
                lines = [
                    line.strip()
                    for line in resp.text.splitlines()
                    if ":" in line and not line.startswith("#")
                ]
                contacts = [
                    c_line.split(":", 1)[1].strip()
                    for c_line in lines
                    if c_line.lower().startswith("contact:")
                ]
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"security.txt Policy Published on '{domain}'",
                        "evidence": f"Found RFC 9116 security policy with contacts: {', '.join(contacts[:2])}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["Standard security.txt file discovered on domain"],
                        "data": {
                            "domain": domain,
                            "contacts": contacts,
                            "raw_preview": resp.text[:300],
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, resp.text[:100]),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No security.txt policy on '{domain}'",
                        "evidence": "Endpoint returned 404 or lacked standard 'Contact:' directives.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["security.txt not published on domain"],
                        "data": {"domain": domain},
                        "evidence_hash": compute_evidence_hash(url, resp.status_code, "not_found"),
                    }
                ]
        except Exception:
            return [
                {
                    **base,
                    "status": FindingStatus.not_found.value,
                    "source_status": SourceStatus.no_match.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"No security.txt policy reachable for '{domain}'",
                    "evidence": "Unable to connect to .well-known/security.txt endpoint.",
                    "confidence": Confidence.low.value,
                    "confidence_reasons": ["Endpoint unreachable"],
                    "data": {"domain": domain},
                    "evidence_hash": compute_evidence_hash(url, None, "unreachable"),
                }
            ]


class EmailCertificateTransparencyModule(OSINTModule):
    """Queries crt.sh Certificate Transparency logs for domain TLS certificates and subdomains."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="email.cert_transparency",
            name="Certificate Transparency Logs (crt.sh)",
            version="1.0.0",
            supported_targets=[TargetType.email],
            source_name="crt.sh CT Log",
            source_url="https://crt.sh",
            description="Searches public certificate transparency logs for domain certificates and SAN subdomains.",
            category="email",
            access_type="public_api",
            limitations=["Passive public certificate log check; no host probing."],
            timeout=10.0,
            license="MIT",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        domain = target.split("@")[-1].strip().lower() if "@" in target else target.strip().lower()
        url = f"https://crt.sh/?q=%25.{domain}&output=json"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://crt.sh/?q=%25.{domain}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=4.0),
                headers={"User-Agent": settings.user_agent},
            ) as client:
                resp = await client.get(url)

            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    subdomains: set[str] = set()
                    for entry in data[:30]:
                        name_value = entry.get("name_value", "")
                        for sub in name_value.splitlines():
                            sub = sub.strip().lower()
                            if domain in sub:
                                subdomains.add(sub)

                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Public TLS Certificates Discovered for '{domain}'",
                            "evidence": f"Found {len(data)} certificate log entries covering {len(subdomains)} subdomains.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["Public certificate transparency logs matched"],
                            "data": {
                                "domain": domain,
                                "total_certificates": len(data),
                                "discovered_subdomains": sorted(list(subdomains))[:15],
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, str(len(data))),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No public certificate logs found for '{domain}'",
                            "evidence": "crt.sh returned empty certificate array.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["No public CT log entries found"],
                            "data": {"domain": domain},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"CT log query returned HTTP {resp.status_code}",
                        "evidence": "Remote CT log service was unavailable or busy.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": [f"HTTP {resp.status_code}"],
                        "data": {"status_code": resp.status_code},
                        "evidence_hash": compute_evidence_hash(url, resp.status_code, None),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Error querying certificate transparency for '{domain}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport failure"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]
