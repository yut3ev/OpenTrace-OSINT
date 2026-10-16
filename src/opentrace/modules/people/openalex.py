"""OpenAlex global scholarly researcher and author search module."""

from __future__ import annotations

import urllib.parse
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


class OpenAlexAuthorModule(OSINTModule):
    """Searches OpenAlex open bibliographic database for academic researchers and citations."""

    _metadata = ModuleMetadata(
        id="name.openalex",
        name="OpenAlex Scholarly Author Search",
        version="0.1.0",
        supported_targets=[TargetType.name],
        source_name="OpenAlex",
        source_url="https://openalex.org",
        description="Searches global academic authors, affiliations, citations, and works on OpenAlex.",
        category="people",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Scholarly authors and researchers; common names produce multiple candidates."
        ],
        timeout=8.0,
        max_requests=1,
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        encoded_query = urllib.parse.quote(target)
        url = f"https://api.openalex.org/authors?search={encoded_query}"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.name.value,
            "search_type": TargetType.name.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://openalex.org/authors?search={encoded_query}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                results = body.get("results", [])

                if results:
                    findings: list[dict[str, Any]] = []
                    top_matches = results[:3]

                    for idx, author in enumerate(top_matches):
                        d_name = author.get("display_name", target)
                        author_id = author.get("id", "")
                        h_index = author.get("summary_stats", {}).get("h_index")
                        works_count = author.get("works_count", 0)
                        last_inst = author.get("last_known_institutions", [])
                        inst_name = last_inst[0].get("display_name") if last_inst else ""

                        evidence_parts = [f"Researcher '{d_name}' found on OpenAlex."]
                        if inst_name:
                            evidence_parts.append(f"Affiliation: {inst_name}.")
                        if works_count:
                            evidence_parts.append(f"Published works: {works_count}.")
                        if h_index is not None:
                            evidence_parts.append(f"h-index: {h_index}.")
                        evidence_parts.append("Candidate match only.")

                        findings.append(
                            {
                                **base,
                                "id": f"{fid}-{idx}",
                                "status": FindingStatus.found.value,
                                "source_status": SourceStatus.succeeded.value,
                                "verification_status": VerificationStatus.candidate.value,
                                "display_name": d_name,
                                "profile_url": author_id,
                                "public_evidence_url": author_id,
                                "title": f"OpenAlex researcher match: '{d_name}'",
                                "evidence": " ".join(evidence_parts),
                                "confidence": Confidence.medium.value,
                                "confidence_reasons": [
                                    "Scholarly author profile returned by OpenAlex bibliographic API"
                                ],
                                "data": {
                                    "id": author_id,
                                    "display_name": d_name,
                                    "institution": inst_name,
                                    "works_count": works_count,
                                    "h_index": h_index,
                                },
                                "evidence_hash": compute_evidence_hash(
                                    author_id, 200, f"openalex:{d_name}"
                                ),
                            }
                        )

                    return findings
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No OpenAlex researcher found for '{target}'",
                            "evidence": f"OpenAlex query returned 0 author profiles matching '{target}'.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": [
                                "Zero results returned from OpenAlex author API"
                            ],
                            "data": {"results": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"OpenAlex API returned status {res.status_code}",
                        "evidence": f"HTTP {res.status_code} received from {url}.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "unknown"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "title": f"OpenAlex search error for '{target}'",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
