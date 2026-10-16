"""Wikipedia notable person and public biographical article search module."""

from __future__ import annotations

import re
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

_TAG_CLEANER = re.compile(r"<.*?>")


def _clean_snippet(snippet: str) -> str:
    return _TAG_CLEANER.sub("", snippet)


class WikipediaPersonModule(OSINTModule):
    """Searches Wikipedia public articles for notable individuals matching a name."""

    _metadata = ModuleMetadata(
        id="name.wikipedia",
        name="Wikipedia Notable People Search",
        version="0.1.0",
        supported_targets=[TargetType.name],
        source_name="Wikipedia",
        source_url="https://en.wikipedia.org/w/api.php",
        description="Searches Wikipedia encyclopedia articles and public biographies matching a person's name.",
        category="people",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=[
            "Covers notable public figures only.",
            "Matching name results are candidates and do not confirm personal identity.",
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
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&utf8=&format=json"
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
            "source_url": f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_query}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                search_results = body.get("query", {}).get("search", [])

                if search_results:
                    top_matches = search_results[:3]
                    findings: list[dict[str, Any]] = []

                    for idx, match in enumerate(top_matches):
                        title = match.get("title", "")
                        snippet = _clean_snippet(match.get("snippet", ""))
                        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"

                        findings.append(
                            {
                                **base,
                                "id": f"{fid}-{idx}",
                                "status": FindingStatus.found.value,
                                "source_status": SourceStatus.succeeded.value,
                                "verification_status": VerificationStatus.candidate.value,
                                "display_name": title,
                                "profile_url": page_url,
                                "public_evidence_url": page_url,
                                "title": f"Wikipedia article candidate: '{title}'",
                                "evidence": f"Wikipedia encyclopedia entry matching '{target}'. Excerpt: \"{snippet}\". Candidate match only.",
                                "confidence": Confidence.medium.value
                                if target.lower() in title.lower()
                                else Confidence.low.value,
                                "confidence_reasons": [
                                    "Public Wikipedia article title or snippet contains query name"
                                ],
                                "data": {
                                    "title": title,
                                    "pageid": match.get("pageid"),
                                    "snippet": snippet,
                                    "url": page_url,
                                },
                                "evidence_hash": compute_evidence_hash(
                                    page_url, 200, f"wiki:{title}"
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
                            "title": f"No Wikipedia biography found for '{target}'",
                            "evidence": f"MediaWiki search returned 0 article results for '{target}'.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": [
                                "Zero results returned from Wikipedia search API"
                            ],
                            "data": {"result_count": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Wikipedia search returned status {res.status_code}",
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
                    "title": f"Wikipedia search error for '{target}'",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
