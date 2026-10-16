"""DNS MX lookup module for email domains."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import dns.exception
import dns.resolver

from opentrace.api.schemas.common import Confidence, FindingStatus, TargetType
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class EmailDNSModule(OSINTModule):
    """Queries DNS MX records for the domain part of an email target."""

    _metadata = ModuleMetadata(
        id="email.dns",
        name="Email Domain DNS MX Lookup",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="DNS MX Records",
        source_url="dns://{domain}/MX",
        description="Queries public DNS Mail Exchanger (MX) records for the email domain.",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "MX records indicate mail server configuration, not mailbox existence.",
            "Some valid domains accept mail on fallback A records without MX.",
            "DNS lookups may be affected by upstream resolver caching or split-horizon DNS.",
        ],
        timeout=5.0,
        max_requests=1,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    def _sync_resolve_mx(self, domain: str) -> list[dict[str, Any]]:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = self.metadata.timeout
        answers = resolver.resolve(domain, "MX")
        records: list[dict[str, Any]] = []
        for rdata in answers:
            records.append(
                {
                    "preference": int(rdata.preference),
                    "exchange": str(rdata.exchange).rstrip("."),
                }
            )
        records.sort(key=lambda r: r["preference"])
        return records

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        finding_id = str(uuid.uuid4())

        if "@" not in target:
            return []

        domain = target.rsplit("@", 1)[1].strip()
        source_url = f"dns://{domain}/MX"

        base_finding: dict[str, Any] = {
            "id": finding_id,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "module_version": self.metadata.version,
            "target_type": TargetType.email.value,
            "observed_at": observed_at,
            "source_name": self.metadata.source_name,
            "source_url": source_url,
        }

        try:
            records = await asyncio.to_thread(self._sync_resolve_mx, domain)
            if records:
                summary = f"mx_found:{len(records)} records for {domain}"
                ev_hash = compute_evidence_hash(source_url, 0, summary)
                exchanges = [f"{r['exchange']} (pri={r['preference']})" for r in records]
                return [
                    {
                        **base_finding,
                        "status": FindingStatus.info.value,
                        "title": f"Mail exchangers found for '{domain}'",
                        "evidence": (
                            f"Domain '{domain}' has {len(records)} configured MX record(s): "
                            f"{', '.join(exchanges)}. "
                            "This verifies mail routing capability, not mailbox existence."
                        ),
                        "confidence": Confidence.medium.value,
                        "data": {
                            "domain": domain,
                            "mx_records": records,
                            "has_mx": True,
                        },
                        "evidence_hash": ev_hash,
                    }
                ]
            else:
                summary = f"no_mx:{domain}"
                ev_hash = compute_evidence_hash(source_url, 0, summary)
                return [
                    {
                        **base_finding,
                        "status": FindingStatus.info.value,
                        "title": f"No MX records found for '{domain}'",
                        "evidence": f"DNS query completed but returned 0 MX records for '{domain}'.",
                        "confidence": Confidence.low.value,
                        "data": {"domain": domain, "mx_records": [], "has_mx": False},
                        "evidence_hash": ev_hash,
                    }
                ]

        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            summary = f"nxdomain_or_no_answer:{domain}"
            ev_hash = compute_evidence_hash(source_url, 0, summary)
            return [
                {
                    **base_finding,
                    "status": FindingStatus.not_found.value,
                    "title": f"No MX records for domain '{domain}'",
                    "evidence": f"DNS query indicated no MX records or domain does not exist ({domain}).",
                    "confidence": Confidence.medium.value,
                    "data": {"domain": domain, "error": "NXDOMAIN or NoAnswer"},
                    "evidence_hash": ev_hash,
                }
            ]
        except dns.exception.Timeout:
            summary = f"timeout:{domain}"
            ev_hash = compute_evidence_hash(source_url, None, summary)
            return [
                {
                    **base_finding,
                    "status": FindingStatus.unknown.value,
                    "title": f"DNS MX lookup timed out for '{domain}'",
                    "evidence": f"DNS server did not respond within {self.metadata.timeout}s timeout.",
                    "confidence": Confidence.none.value,
                    "data": {"domain": domain, "error": "timeout"},
                    "evidence_hash": ev_hash,
                }
            ]
        except Exception as exc:
            summary = f"dns_error:{type(exc).__name__}:{str(exc)}"
            ev_hash = compute_evidence_hash(source_url, None, summary)
            return [
                {
                    **base_finding,
                    "status": FindingStatus.unknown.value,
                    "title": f"DNS MX lookup error for '{domain}'",
                    "evidence": f"DNS query error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"domain": domain, "error": str(exc)},
                    "evidence_hash": ev_hash,
                }
            ]
