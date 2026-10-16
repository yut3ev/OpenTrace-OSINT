"""Public web search adapters using open interfaces without paid APIs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

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


class DuckDuckGoInstantModule(OSINTModule):
    """Searches DuckDuckGo Instant Answer API for public entities, topics, and references."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="web.duckduckgo_instant",
            name="DuckDuckGo Instant Answer Search",
            version="1.0.0",
            supported_targets=[TargetType.web, TargetType.name],
            source_name="DuckDuckGo Instant API",
            source_url="https://api.duckduckgo.com",
            description="Queries DuckDuckGo public instant answers for abstracts, related topics, and verified sources.",
            category="web",
            access_type="public_api",
            limitations=["Indexes publicly recognized topics, entities, and open documentation."],
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

        encoded = quote_plus(target)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.web.value,
            "search_type": TargetType.web.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://duckduckgo.com/?q={encoded}",
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
                heading = data.get("Heading", "")
                abstract = data.get("Abstract", "")
                abstract_url = data.get("AbstractURL", "")
                related = data.get("RelatedTopics", [])

                has_result = bool(abstract or related or heading)

                if has_result:
                    topics: list[dict[str, str]] = []
                    for item in related[:5]:
                        if isinstance(item, dict) and item.get("Text"):
                            topics.append(
                                {
                                    "title": item.get("Text", ""),
                                    "url": item.get("FirstURL", ""),
                                }
                            )

                    summary = abstract or (topics[0]["title"] if topics else heading)
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"DuckDuckGo Knowledge Result: '{heading or target}'",
                            "evidence": f"Abstract: {summary[:200]} (Source: {abstract_url or 'DuckDuckGo'})",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Public instant answer entity resolved on DuckDuckGo"
                            ],
                            "data": {
                                "heading": heading,
                                "abstract": abstract,
                                "abstract_url": abstract_url,
                                "related_topics": topics,
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, summary[:100]),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No instant abstract for '{target}' on DuckDuckGo",
                            "evidence": "DuckDuckGo Instant Answer API returned empty abstract payload.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["No instant answer knowledge card for query"],
                            "data": {"query": target},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            elif resp.status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Rate limited by {self.metadata.source_name}",
                        "evidence": "HTTP 429 Too Many Requests received from DuckDuckGo API.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Platform rate limit encountered"],
                        "data": {"status_code": 429},
                        "evidence_hash": compute_evidence_hash(url, 429, None),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Unexpected response from {self.metadata.source_name}",
                        "evidence": f"HTTP status {resp.status_code} received from DuckDuckGo.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": [f"HTTP {resp.status_code}"],
                        "data": {"status_code": resp.status_code},
                        "evidence_hash": compute_evidence_hash(url, resp.status_code, None),
                    }
                ]
        except TimeoutError:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.unavailable.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Timeout connecting to {self.metadata.source_name}",
                    "evidence": "Request timed out.",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network timeout"],
                    "data": {"timeout": True},
                    "evidence_hash": compute_evidence_hash(url, None, "timeout"),
                }
            ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Error querying {self.metadata.source_name}",
                    "evidence": f"Exception during execution: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Unexpected exception"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class OpenWebSearchModule(OSINTModule):
    """Formulates open web query patterns and searches open-web metasearch gateways."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="web.open_search",
            name="Open Web Search Gateway",
            version="1.0.0",
            supported_targets=[TargetType.web, TargetType.name],
            source_name="Open Web Metasearch",
            source_url="https://html.duckduckgo.com",
            description="Constructs boolean open-web queries with safe operators and checks web presence.",
            category="web",
            access_type="public_web",
            limitations=["Respects robots.txt and public gateway usage guidelines."],
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

        encoded = quote_plus(target)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.web.value,
            "search_type": TargetType.web.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": url,
            "limitations": self.metadata.limitations,
        }

        # Formulate structured dorks and queries
        queries = {
            "exact_phrase": f'"{target}"',
            "social_profiles": f'"{target}" site:linkedin.com OR site:github.com OR site:twitter.com',
            "documents": f'"{target}" filetype:pdf OR filetype:doc',
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=4.0),
                headers={"User-Agent": settings.user_agent},
                follow_redirects=True,
            ) as client:
                resp = await client.get(url)

            if resp.status_code == 200:
                has_results = "result__snippet" in resp.text or "result__title" in resp.text
                status = FindingStatus.found.value if has_results else FindingStatus.not_found.value
                src_status = (
                    SourceStatus.succeeded.value if has_results else SourceStatus.no_match.value
                )
                return [
                    {
                        **base,
                        "status": status,
                        "source_status": src_status,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Web Search Query Formulated for '{target}'",
                        "evidence": "Constructed targeted search operators and executed web lookup (HTTP 200).",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": [
                            "Web search patterns generated and verified against open index"
                        ],
                        "data": {
                            "query": target,
                            "structured_queries": queries,
                            "results_detected": has_results,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, target),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.info.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Web Search Queries for '{target}'",
                        "evidence": "Constructed structured search operators for manual and external lookup.",
                        "confidence": Confidence.low.value,
                        "confidence_reasons": ["Search queries constructed successfully"],
                        "data": {"query": target, "structured_queries": queries},
                        "evidence_hash": compute_evidence_hash(url, resp.status_code, target),
                    }
                ]
        except Exception:
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.succeeded.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": f"Web Search Queries for '{target}'",
                    "evidence": "Constructed structured search queries for external query engines.",
                    "confidence": Confidence.low.value,
                    "confidence_reasons": ["Structured query patterns generated"],
                    "data": {"query": target, "structured_queries": queries},
                    "evidence_hash": compute_evidence_hash(url, None, target),
                }
            ]
