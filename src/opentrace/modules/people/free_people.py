"""Free public people, biographical, and scholar modules without paid APIs."""

from __future__ import annotations

import re
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


class WikidataEntityModule(OSINTModule):
    """Searches official Wikidata entity registry for biographical records and notability descriptors."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="name.wikidata",
            name="Wikidata Biographical Entities",
            version="1.0.0",
            supported_targets=[TargetType.name],
            source_name="Wikidata Public Knowledge Base",
            source_url="https://www.wikidata.org",
            description="Queries Wikidata entity search for biographical entries, aliases, and descriptions.",
            category="people",
            access_type="public_api",
            limitations=["Biographical entities reflect public notability on Wikimedia projects."],
            timeout=8.0,
            license="CC0",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        encoded = quote_plus(target)
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={encoded}&language=en&format=json"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.name.value,
            "search_type": TargetType.name.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://www.wikidata.org/wiki/Special:Search?search={encoded}",
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
                results = data.get("search", [])
                if results and len(results) > 0:
                    top = results[0]
                    qid = top.get("id", "")
                    label = top.get("label", target)
                    description = top.get("description", "Wikidata entity")
                    concept_url = top.get("concepturi", f"https://www.wikidata.org/wiki/{qid}")

                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Wikidata Entity: {label} ({qid})",
                            "evidence": f"Wikidata entry '{label}': {description}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Direct Wikidata entity match with official concept URI"
                            ],
                            "data": {
                                "qid": qid,
                                "label": label,
                                "description": description,
                                "url": concept_url,
                                "matches_count": len(results),
                            },
                            "evidence_hash": compute_evidence_hash(
                                concept_url, 200, f"{qid}:{description}"
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
                            "title": f"No Wikidata entity found for '{target}'",
                            "evidence": "Wikidata entity search returned 0 items.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": [
                                "No entity with matching label in Wikidata catalog"
                            ],
                            "data": {"query": target},
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
                        "title": f"Wikidata returned HTTP {resp.status_code}",
                        "evidence": "Remote Wikidata API was unavailable.",
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
                    "title": f"Error querying Wikidata for '{target}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport failure"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class SemanticScholarAuthorModule(OSINTModule):
    """Searches Semantic Scholar public academic graph for author bibliometrics and papers."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="name.semantic_scholar",
            name="Semantic Scholar Academic Authors",
            version="1.0.0",
            supported_targets=[TargetType.name],
            source_name="Semantic Scholar Graph API",
            source_url="https://api.semanticscholar.org",
            description="Searches Semantic Scholar graph for author publications, affiliations, and citation metrics.",
            category="people",
            access_type="public_api",
            limitations=[
                "Scholarly research publications only; does not index non-academic persons."
            ],
            timeout=8.0,
            license="ODC-BY",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        encoded = quote_plus(target)
        url = f"https://api.semanticscholar.org/graph/v1/author/search?query={encoded}&fields=name,aliases,affiliations,paperCount,citationCount,hIndex&limit=3"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.name.value,
            "search_type": TargetType.name.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://www.semanticscholar.org/search?q={encoded}&sort=relevance",
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
                authors = data.get("data", [])
                if authors and len(authors) > 0:
                    author = authors[0]
                    author_id = author.get("authorId", "")
                    name = author.get("name", target)
                    papers = author.get("paperCount", 0)
                    citations = author.get("citationCount", 0)
                    h_index = author.get("hIndex", 0)
                    affiliations = author.get("affiliations", [])

                    profile_url = f"https://www.semanticscholar.org/author/{author_id}"
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Semantic Scholar Author: {name}",
                            "evidence": f"Found author record with {papers} paper(s), {citations} citation(s), h-index: {h_index}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Semantic Scholar academic graph author record match"
                            ],
                            "data": {
                                "author_id": author_id,
                                "name": name,
                                "paper_count": papers,
                                "citation_count": citations,
                                "h_index": h_index,
                                "affiliations": affiliations,
                                "profile_url": profile_url,
                            },
                            "evidence_hash": compute_evidence_hash(
                                profile_url, 200, f"{author_id}:{papers}"
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
                            "title": f"No academic author found for '{target}' on Semantic Scholar",
                            "evidence": "Semantic Scholar author search returned 0 records.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["No author record found in academic database"],
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
                        "evidence": "HTTP 429 Too Many Requests from Semantic Scholar API.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["API rate limit exceeded"],
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
                        "title": f"Semantic Scholar returned HTTP {resp.status_code}",
                        "evidence": "Remote API returned non-success status.",
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
                    "title": f"Error querying Semantic Scholar for '{target}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport failure"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class WikipediaFullTextSearchModule(OSINTModule):
    """Searches Wikipedia full-text search API for encyclopedic mentions and biographical article matches."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="name.wikipedia_search",
            name="Wikipedia Full-Text Article Search",
            version="1.0.0",
            supported_targets=[TargetType.name],
            source_name="Wikipedia Search API",
            source_url="https://en.wikipedia.org",
            description="Performs full-text encyclopedic article search across English Wikipedia.",
            category="people",
            access_type="public_api",
            limitations=["Searches article text; subject to encyclopedic notability thresholds."],
            timeout=8.0,
            license="CC BY-SA",
            requires_api_key=False,
            is_free=True,
        )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        encoded = quote_plus(target)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&format=json&srlimit=3"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.name.value,
            "search_type": TargetType.name.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}",
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
                search_results = data.get("query", {}).get("search", [])
                if search_results and len(search_results) > 0:
                    top = search_results[0]
                    title = top.get("title", "")
                    raw_snippet = top.get("snippet", "")
                    clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet)
                    page_url = (
                        f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    )

                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Wikipedia Article Match: '{title}'",
                            "evidence": f"Found article '{title}': {clean_snippet[:200]}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Full-text Wikipedia article title and snippet match"
                            ],
                            "data": {
                                "title": title,
                                "snippet": clean_snippet,
                                "page_url": page_url,
                                "wordcount": top.get("wordcount", 0),
                            },
                            "evidence_hash": compute_evidence_hash(page_url, 200, title),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No Wikipedia article found for '{target}'",
                            "evidence": "Wikipedia full-text search returned 0 results.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["No matching articles found in Wikipedia"],
                            "data": {"query": target},
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
                        "title": f"Wikipedia search returned HTTP {resp.status_code}",
                        "evidence": "Remote Wikipedia API was unavailable.",
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
                    "title": f"Error querying Wikipedia search for '{target}'",
                    "evidence": f"Exception: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport failure"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]
