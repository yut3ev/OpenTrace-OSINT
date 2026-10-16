"""Extended people, academic research, and public search provider modules."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

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


class CrossrefAuthorModule(OSINTModule):
    """Searches CrossRef scholarly database for authors by full name."""

    metadata = ModuleMetadata(
        id="people.crossref",
        name="CrossRef Author Search",
        version="1.0.0",
        supported_targets=[TargetType.name],
        source_name="CrossRef",
        source_url="https://api.crossref.org/works",
        description="Searches international published scholarly articles and author citations by name.",
        category="people",
        access_type="public_api",
        limitations=[
            "Common names may yield multiple distinct individuals (disambiguation required)"
        ],
        timeout=10.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = f"https://api.crossref.org/works?query.author={quote(target)}&rows=5"

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
            "source_url": "https://search.crossref.org",
            "limitations": self.metadata.limitations,
        }

        headers = {"User-Agent": f"{settings.user_agent} (mailto:research@opentrace-osint.local)"}

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                total_results = data.get("message", {}).get("total-results", 0)
                items = data.get("message", {}).get("items", [])

                if total_results > 0 and items:
                    sample_titles = [" ".join(i.get("title", ["Untitled"])) for i in items[:3]]
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Indexed author in CrossRef ({total_results} works)",
                            "evidence": (
                                f"Found {total_results} scholarly work(s) authored by '{target}'. "
                                f"Recent: '{sample_titles[0]}'."
                            ),
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Peer-reviewed publication indexed in official CrossRef repository"
                            ],
                            "data": {
                                "total_works": total_results,
                                "sample_titles": sample_titles,
                            },
                            "evidence_hash": compute_evidence_hash(
                                url, 200, f"works:{total_results}"
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
                            "title": f"No CrossRef publications for '{target}'",
                            "evidence": "CrossRef author search returned zero publications.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["Total results is 0 in CrossRef"],
                            "data": {"total_works": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "total:0"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"CrossRef API error HTTP {res.status_code}",
                        "evidence": "Remote server returned non-200 status code.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["API response code"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, None),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Error connecting to CrossRef author API",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class ArxivAuthorModule(OSINTModule):
    """Searches scientific preprints on arXiv.org for author matches."""

    metadata = ModuleMetadata(
        id="people.arxiv",
        name="arXiv Scientific Preprints",
        version="1.0.0",
        supported_targets=[TargetType.name],
        source_name="arXiv",
        source_url="https://arxiv.org",
        description="Searches open scientific preprints in physics, math, computer science, and quantitative biology.",
        category="people",
        access_type="public_api",
        limitations=["Returns matching authors across historical preprint archive"],
        timeout=10.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = f"https://export.arxiv.org/api/query?search_query=au:{quote(target)}&max_results=3"

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
            "source_url": f"https://arxiv.org/search/?searchtype=author&query={quote(target)}",
            "limitations": self.metadata.limitations,
        }

        headers = {"User-Agent": settings.user_agent}

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                res = await client.get(url)

            if res.status_code == 200:
                body = res.text
                has_entry = "<entry>" in body
                if has_entry:
                    # Extract sample paper title
                    import re

                    titles = re.findall(r"<title>(.*?)</title>", body, re.DOTALL)
                    paper_title = titles[-1].strip() if titles else "Scientific Preprint"

                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Preprint author on arXiv ('{paper_title}')",
                            "evidence": f"Found preprint author record on arXiv.org for '{target}'. Paper: '{paper_title}'.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Preprint metadata in Cornell University arXiv repository"
                            ],
                            "data": {"sample_paper": paper_title},
                            "evidence_hash": compute_evidence_hash(url, 200, paper_title),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No arXiv preprints found for '{target}'",
                            "evidence": "arXiv query returned zero author matches.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["arXiv Atom feed contains zero entry items"],
                            "data": {},
                            "evidence_hash": compute_evidence_hash(url, 200, "no_entries"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"arXiv API error HTTP {res.status_code}",
                        "evidence": "Remote arXiv API returned non-200 status code.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["API response code"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, None),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.error.value,
                    "source_status": SourceStatus.error.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Error connecting to arXiv API",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class SearchQueryGeneratorModule(OSINTModule):
    """Generates targeted, lawful public web search engine queries and direct verification URLs."""

    metadata = ModuleMetadata(
        id="people.search_query",
        name="Public Search Engine Query Generator",
        version="1.0.0",
        supported_targets=[TargetType.name],
        source_name="Public Web Query Generator",
        source_url="https://duckduckgo.com",
        description="Generates precision search dorks and lawful public web links for Google, DuckDuckGo, and LinkedIn.",
        category="people",
        access_type="local_analysis",
        limitations=[
            "Provides query formulas and search links; does not scrape private search results"
        ],
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

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
            "source_url": self.metadata.source_url,
            "limitations": self.metadata.limitations,
        }

        clean_name = target.strip()
        encoded = quote(f'"{clean_name}"')
        ddg_url = f"https://duckduckgo.com/?q={encoded}"
        google_url = f"https://www.google.com/search?q={encoded}"
        linkedin_query = f"https://www.google.com/search?q=site%3Alinkedin.com%2Fin+{encoded}"
        github_query = f"https://github.com/search?q={quote(clean_name)}&type=users"

        return [
            {
                **base,
                "status": FindingStatus.found.value,
                "source_status": SourceStatus.succeeded.value,
                "verification_status": VerificationStatus.verified.value,
                "title": f"Public search engine queries formulated for '{clean_name}'",
                "evidence": (
                    f"Generated structured precision search queries for '{clean_name}'. "
                    f"Direct verification links prepared for DuckDuckGo, Google, LinkedIn, and GitHub."
                ),
                "confidence": Confidence.high.value,
                "confidence_reasons": [
                    "Syntactically verified precision search query formulations"
                ],
                "data": {
                    "duckduckgo_url": ddg_url,
                    "google_url": google_url,
                    "linkedin_search_url": linkedin_query,
                    "github_search_url": github_query,
                },
                "evidence_hash": compute_evidence_hash("search:queries", 200, clean_name),
            }
        ]
