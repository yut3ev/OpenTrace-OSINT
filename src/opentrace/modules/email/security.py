"""Domain SPF and DMARC security record inspection module."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import dns.resolver

from opentrace.api.schemas.common import (
    Confidence,
    FindingStatus,
    SourceStatus,
    TargetType,
    VerificationStatus,
)
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule


class EmailSecurityModule(OSINTModule):
    """Inspects SPF (Sender Policy Framework) and DMARC records for the email domain."""

    _metadata = ModuleMetadata(
        id="email.security",
        name="Domain SPF & DMARC Security",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="DNS TXT Records",
        source_url="dns://{domain}/TXT",
        description="Inspects SPF and DMARC email spoofing protection policies for the domain.",
        category="email",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Evaluates domain email protection configuration, not individual account."],
        timeout=5.0,
        max_requests=2,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    def _sync_query_security(self, domain: str) -> dict[str, Any]:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = self.metadata.timeout
        spf_record = None
        dmarc_record = None

        # Check SPF on apex domain
        try:
            answers = resolver.resolve(domain, "TXT")
            for rdata in answers:
                txt = "".join(
                    s.decode("utf-8", errors="ignore") if isinstance(s, bytes) else str(s)
                    for s in rdata.strings
                )
                if txt.startswith("v=spf1"):
                    spf_record = txt
                    break
        except Exception:
            pass

        # Check DMARC on _dmarc.domain
        try:
            dmarc_answers = resolver.resolve(f"_dmarc.{domain}", "TXT")
            for rdata in dmarc_answers:
                txt = "".join(
                    s.decode("utf-8", errors="ignore") if isinstance(s, bytes) else str(s)
                    for s in rdata.strings
                )
                if txt.startswith("v=DMARC1"):
                    dmarc_record = txt
                    break
        except Exception:
            pass

        return {"spf": spf_record, "dmarc": dmarc_record}

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        if "@" not in target:
            return []

        domain = target.rsplit("@", 1)[1].strip()
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
            "source_url": f"dns://{domain}/TXT",
            "limitations": self.metadata.limitations,
        }

        try:
            records = await asyncio.to_thread(self._sync_query_security, domain)
            spf = records.get("spf")
            dmarc = records.get("dmarc")

            has_security = bool(spf or dmarc)
            details = []
            if spf:
                details.append(f"SPF: {spf}")
            else:
                details.append("SPF: No record found")
            if dmarc:
                details.append(f"DMARC: {dmarc}")
            else:
                details.append("DMARC: No policy record found")

            summary = f"spf:{bool(spf)}|dmarc:{bool(dmarc)}"
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.succeeded.value,
                    "verification_status": VerificationStatus.verified.value
                    if has_security
                    else VerificationStatus.unverified.value,
                    "title": f"Domain security for '{domain}': {'Configured' if has_security else 'Missing policies'}",
                    "evidence": f"DNS security check for '{domain}'. " + "; ".join(details) + ".",
                    "confidence": Confidence.high.value
                    if has_security
                    else Confidence.medium.value,
                    "confidence_reasons": [
                        "Direct DNS TXT query for SPF and _dmarc records completed"
                    ],
                    "data": {
                        "domain": domain,
                        "has_spf": bool(spf),
                        "has_dmarc": bool(dmarc),
                        "spf": spf,
                        "dmarc": dmarc,
                    },
                    "evidence_hash": compute_evidence_hash(f"dns://{domain}/TXT", 200, summary),
                }
            ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "title": f"Domain security check error for '{domain}'",
                    "evidence": f"DNS error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(
                        f"dns://{domain}/TXT", None, f"error:{exc}"
                    ),
                }
            ]
