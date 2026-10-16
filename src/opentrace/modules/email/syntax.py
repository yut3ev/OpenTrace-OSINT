"""Email syntax validation and structural analysis module."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from opentrace.api.schemas.common import Confidence, FindingStatus, TargetType
from opentrace.core.evidence import compute_evidence_hash
from opentrace.modules.base import ModuleMetadata, OSINTModule

_EMAIL_PATTERN = re.compile(
    r"^(?P<local>[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+)@(?P<domain>[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+)$"
)


class EmailSyntaxModule(OSINTModule):
    """Validates email address syntax and extracts structural parts."""

    _metadata = ModuleMetadata(
        id="email.syntax",
        name="Email Syntax Validation",
        version="0.1.0",
        supported_targets=[TargetType.email],
        source_name="RFC 5321/5322 Standards",
        source_url="https://datatracker.ietff.org/doc/html/rfc5321",
        description="Analyzes email address syntax and structural components.",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Syntax correctness does not imply mailbox exists or can receive mail.",
            "Does not connect to mail servers or verify recipient.",
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
            "target_type": TargetType.email.value,
            "observed_at": observed_at,
            "source_name": self.metadata.source_name,
            "source_url": self.metadata.source_url,
        }

        match = _EMAIL_PATTERN.match(target)
        if not match:
            ev_hash = compute_evidence_hash(
                self.metadata.source_url, None, f"invalid_syntax:{target}"
            )
            return [
                {
                    **base_finding,
                    "status": FindingStatus.error.value,
                    "title": f"Invalid email syntax: '{target}'",
                    "evidence": "Email address does not conform to RFC 5321/5322 syntax specifications.",
                    "confidence": Confidence.none.value,
                    "data": {"valid": False, "raw": target},
                    "evidence_hash": ev_hash,
                }
            ]

        local_part = match.group("local")
        domain_part = match.group("domain")

        try:
            ascii_domain = domain_part.encode("idna").decode("ascii")
        except Exception:
            ascii_domain = domain_part

        data = {
            "valid": True,
            "local_part": local_part,
            "domain": domain_part,
            "ascii_domain": ascii_domain,
            "length": len(target),
            "is_subdomain": domain_part.count(".") > 1,
        }

        summary = f"syntax_ok:{local_part}@{domain_part}"
        ev_hash = compute_evidence_hash(self.metadata.source_url, 0, summary)

        return [
            {
                **base_finding,
                "status": FindingStatus.info.value,
                "title": f"Valid email format: '{target}'",
                "evidence": (
                    f"Syntax conforms to RFC specifications. Local part: '{local_part}', "
                    f"Domain: '{domain_part}'. Note: This does NOT indicate mailbox existence."
                ),
                "confidence": Confidence.high.value,
                "data": data,
                "evidence_hash": ev_hash,
            }
        ]
