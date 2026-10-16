"""DBLP Computer Science Bibliography author search module."""

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


class DblpAuthorModule(OSINTModule):
    """Searches DBLP computer science bibliography for published scholarly researchers."""

    _metadata = ModuleMetadata(
        id="name.dblp",
        name="DBLP Computer Science Bibliography",
        version="0.1.0",
        supported_targets=[TargetType.name],
        source_name="DBLP",
        source_url="https://dblp.org",
        description="Searches public computer science authors, citations, and publication profiles on DBLP.",
        category="people",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Academic authors in computer science and engineering only."],
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
        url = f"https://dblp.org/search/author/api?q={encoded_query}&format=json"
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
            "source_url": f"https://dblp.org/search?q={encoded_query}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                hits = body.get("result", {}).get("hits", {}).get("hit", [])

                if hits:
                    findings: list[dict[str, Any]] = []
                    top_hits = hits[:3]

                    for idx, hit in enumerate(top_hits):
                        info = hit.get("info", {})
                        author_name = info.get("author", target)
                        author_url = info.get("url", "")
                        notes = info.get("notes", {})
                        affiliation = ""
                        if isinstance(notes, dict):
                            note_items = notes.get("note", [])
                            if isinstance(note_items, list) and note_items:
                                affiliation = note_items[0].get("text", "")
                            elif isinstance(note_items, dict):
                                affiliation = note_items.get("text", "")

                        evidence_text = f"Scholarly author index on DBLP matching '{target}'. Listed as: '{author_name}'."
                        if affiliation:
                            evidence_text += f" Affiliation: {affiliation}."

                        findings.append(
                            {
                                **base,
                                "id": f"{fid}-{idx}",
                                "status": FindingStatus.found.value,
                                "source_status": SourceStatus.succeeded.value,
                                "verification_status": VerificationStatus.candidate.value,
                                "display_name": author_name,
                                "profile_url": author_url,
                                "public_evidence_url": author_url,
                                "title": f"DBLP author match: '{author_name}'",
                                "evidence": evidence_text,
                                "confidence": Confidence.medium.value,
                                "confidence_reasons": [
                                    "Published author record found in DBLP scholarly database"
                                ],
                                "data": {
                                    "author": author_name,
                                    "url": author_url,
                                    "affiliation": affiliation,
                                },
                                "evidence_hash": compute_evidence_hash(
                                    author_url, 200, f"dblp:{author_name}"
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
                            "title": f"No DBLP author found for '{target}'",
                            "evidence": f"DBLP bibliography search returned 0 author records for '{target}'.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["Zero hits in DBLP author API query"],
                            "data": {"hits": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"DBLP API returned status {res.status_code}",
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
                    "title": f"DBLP search error for '{target}'",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
