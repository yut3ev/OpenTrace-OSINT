"""Disposable and temporary email provider detection module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from opentrace.api.schemas.common import (
    Confidence,
    FindingStatus,
    SourceStatus,
    TargetType,
    VerificationStatus,
)
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule

# Curated set of popular temporary and throwaway email services
_DISPOSABLE_DOMAINS = frozenset(
    [
        "mailinator.com",
        "guerrillamail.com",
        "sharklasers.com",
        "grr.la",
        "guerrillamail.biz",
        "guerrillamail.de",
        "guerrillamail.net",
        "guerrillamail.org",
        "10minutemail.com",
        "10minutemail.net",
        "tempmail.com",
        "temp-mail.org",
        "tempmailo.com",
        "yopmail.com",
        "yopmail.fr",
        "yopmail.net",
        "trashmail.com",
        "trashmail.net",
        "trashmail.me",
        "dispostable.com",
        "getairmail.com",
        "fakemailgenerator.com",
        "throwawaymail.com",
        "maildrop.cc",
        "inboxkitten.com",
        "mohmal.com",
        "crazymailing.com",
        "nada.ltd",
        "getnada.com",
        "tempail.com",
        "burnermail.io",
        "mytemp.email",
        "luxusmail.org",
        "emailondeck.com",
        "generatorsmail.com",
        "fakemail.net",
        "incognitomail.org",
        "clipmail.eu",
        "dropmail.me",
        "minuteinbox.com",
        "guerrillamailblock.com",
        "pokemail.net",
        "spam4.me",
        "bccto.me",
        "chacuo.net",
        "0815.ru",
        "armyspy.com",
        "cuvox.de",
        "dayrep.com",
        "fleckens.hu",
        "gustr.com",
        "jourrapide.com",
        "rhyta.com",
        "superrito.com",
        "teleworm.us",
        "einrot.com",
        "nowmymail.com",
        "trbvm.com",
        "mailnesia.com",
        "meltmail.com",
        "spambox.us",
        "binkmail.com",
        "safetymail.info",
    ]
)


class DisposableEmailModule(OSINTModule):
    """Detects whether an email address utilizes a known temporary or disposable domain."""

    _metadata = ModuleMetadata(
        id="email.disposable",
        name="Disposable Email Check",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="Disposable Email Registry",
        source_url="https://github.com/disposable-email-domains/disposable-email-domains",
        description="Identifies throwaway, disposable, and temporary mailbox providers.",
        category="email",
        access_type="local_analysis",
        enabled=True,
        implementation_status="implemented",
        limitations=["Maintains local catalog of known disposable email providers."],
        timeout=1.0,
        max_requests=0,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        if "@" not in target:
            return []

        domain = target.rsplit("@", 1)[1].strip().lower()
        is_disposable = domain in _DISPOSABLE_DOMAINS

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
            "source_url": f"domain://{domain}",
            "limitations": self.metadata.limitations,
        }

        if is_disposable:
            return [
                {
                    **base,
                    "status": FindingStatus.found.value,
                    "source_status": SourceStatus.succeeded.value,
                    "verification_status": VerificationStatus.verified.value,
                    "title": f"Disposable email domain detected: '{domain}'",
                    "evidence": f"Domain '{domain}' matches a known temporary disposable mailbox service. Account may be ephemeral.",
                    "confidence": Confidence.high.value,
                    "confidence_reasons": [
                        "Domain matched curated disposable mail provider registry"
                    ],
                    "data": {"domain": domain, "is_disposable": True},
                    "evidence_hash": compute_evidence_hash(
                        f"domain://{domain}", 200, "disposable:true"
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
                    "title": f"Standard email domain: '{domain}'",
                    "evidence": f"Domain '{domain}' is not in the known disposable email blocklist.",
                    "confidence": Confidence.medium.value,
                    "confidence_reasons": ["Domain not found in disposable email database"],
                    "data": {"domain": domain, "is_disposable": False},
                    "evidence_hash": compute_evidence_hash(
                        f"domain://{domain}", 200, "disposable:false"
                    ),
                }
            ]
