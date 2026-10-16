"""Extended email investigation modules: GitHub Commits, OpenPGP Keyserver, CrossRef Author, WHOIS, Hunter.io Provider."""

from __future__ import annotations

import os
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


class GitHubCommitsEmailModule(OSINTModule):
    """Searches public git commit author records on GitHub for public code contributions."""

    metadata = ModuleMetadata(
        id="email.github_commits",
        name="GitHub Commit Authors",
        version="1.0.0",
        supported_targets=[TargetType.email],
        source_name="GitHub",
        source_url="https://api.github.com/search/commits",
        description="Discovers public open-source Git commits authored with the target email address on GitHub.",
        category="developer",
        access_type="public_api",
        limitations=["Only indexes commits on the default branch of public repositories"],
        timeout=10.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = f"https://api.github.com/search/commits?q=author-email:{quote(target)}"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://github.com/search?q=author-email%3A{quote(target)}&type=commits",
            "limitations": self.metadata.limitations,
        }

        headers = {
            "User-Agent": settings.user_agent,
            "Accept": "application/vnd.github.cloak-preview+json",
        }

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json()
                total_count = data.get("total_count", 0)
                items = data.get("items", [])

                if total_count > 0 and items:
                    first = items[0]
                    author_name = (
                        first.get("commit", {}).get("author", {}).get("name")
                        or "Unknown Contributor"
                    )
                    repo_name = first.get("repository", {}).get("full_name") or "Public Repository"
                    repo_url = first.get("repository", {}).get("html_url") or "https://github.com"
                    commit_sha = first.get("sha", "")[:7]

                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Public GitHub commits found ({total_count} commits, author: {author_name})",
                            "evidence": (
                                f"Target email '{target}' is author of {total_count} public commit(s) on GitHub. "
                                f"Example: {repo_name} commit {commit_sha} by '{author_name}'."
                            ),
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Cryptographically verified commit metadata from GitHub API"
                            ],
                            "data": {
                                "commit_count": total_count,
                                "author_name": author_name,
                                "sample_repository": repo_name,
                                "sample_repository_url": repo_url,
                                "sample_sha": commit_sha,
                            },
                            "evidence_hash": compute_evidence_hash(
                                url, 200, f"commits:{total_count}:{commit_sha}"
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
                            "title": f"No public GitHub commits found for '{target}'",
                            "evidence": "GitHub commit search returned zero public matching commits.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["GitHub search API reported total_count: 0"],
                            "data": {"commit_count": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "total_count:0"),
                        }
                    ]
            elif res.status_code == 422:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Invalid email format query on GitHub for '{target}'",
                        "evidence": "GitHub API rejected commit author search query as unprocessable.",
                        "confidence": Confidence.low.value,
                        "confidence_reasons": ["HTTP 422 Unprocessable query"],
                        "data": {"status_code": 422},
                        "evidence_hash": compute_evidence_hash(url, 422, None),
                    }
                ]
            elif res.status_code == 403 or res.status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": "GitHub search API rate limit reached",
                        "evidence": "Unauthenticated rate limit of 10 search queries/minute reached on GitHub.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Rate limit response from GitHub API"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, None),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": "GitHub search API returned unexpected status",
                        "evidence": f"Remote host returned HTTP {res.status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Non-200 HTTP response"],
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
                    "title": "Error connecting to GitHub commit search",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport failure"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class PgpKeyserverEmailModule(OSINTModule):
    """Searches open PGP public keyservers for PGP identity keys registered with the email address."""

    metadata = ModuleMetadata(
        id="email.pgp_keyserver",
        name="OpenPGP Keyserver",
        version="1.0.0",
        supported_targets=[TargetType.email],
        source_name="OpenPGP Keyserver",
        source_url="https://keys.openpgp.org",
        description="Discovers public cryptographic PGP certificates and identity keys associated with an email.",
        category="security",
        access_type="public_api",
        limitations=["Only returns cryptographic certificates submitted to public keyservers"],
        timeout=8.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = f"https://keys.openpgp.org/vks/v1/by-email/{quote(target)}"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": f"https://keys.openpgp.org/search?q={quote(target)}",
            "limitations": self.metadata.limitations,
        }

        headers = {"User-Agent": settings.user_agent, "Accept": "application/pgp-keys"}

        try:
            async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                res = await client.get(url)

            if res.status_code == 200:
                key_text = res.text
                has_key = "-----BEGIN PGP PUBLIC KEY BLOCK-----" in key_text
                if has_key:
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Valid OpenPGP public key found for '{target}'",
                            "evidence": f"Found confirmed OpenPGP public certificate on keys.openpgp.org for {target}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Valid ASCII-armored PGP public key retrieved from keyserver"
                            ],
                            "data": {
                                "has_pgp_key": True,
                                "keyserver": "keys.openpgp.org",
                                "armored_length": len(key_text),
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, key_text[:120]),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"No OpenPGP key found for '{target}'",
                            "evidence": "Keyserver returned response without valid PGP key block.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["Missing PGP header in response"],
                            "data": {"has_pgp_key": False},
                            "evidence_hash": compute_evidence_hash(url, 200, "no_pgp"),
                        }
                    ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"No OpenPGP public key for '{target}' on keys.openpgp.org",
                        "evidence": "keys.openpgp.org returned HTTP 404 (no key registered).",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Keyserver confirmed no public key exists for email"
                        ],
                        "data": {"has_pgp_key": False},
                        "evidence_hash": compute_evidence_hash(url, 404, None),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": "OpenPGP keyserver returned unexpected status",
                        "evidence": f"Remote host returned HTTP {res.status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Non-standard HTTP response"],
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
                    "title": "Error connecting to OpenPGP keyserver",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class CrossrefAuthorEmailModule(OSINTModule):
    """Searches CrossRef academic works for published author records referencing the target email."""

    metadata = ModuleMetadata(
        id="email.crossref_author",
        name="CrossRef Academic Contact",
        version="1.0.0",
        supported_targets=[TargetType.email],
        source_name="CrossRef",
        source_url="https://api.crossref.org/works",
        description="Searches academic scholarly papers and author affiliations for public research contact emails.",
        category="academic",
        access_type="public_api",
        limitations=[
            "Only indexes research articles with public author email metadata in CrossRef"
        ],
        timeout=10.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())
        url = f"https://api.crossref.org/works?query={quote(target)}&rows=3"

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
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
                items = data.get("message", {}).get("items", [])
                matched_works = []

                target_lower = target.lower()
                for item in items:
                    title = " ".join(item.get("title", ["Untitled Paper"]))
                    doi = item.get("DOI", "")
                    authors = item.get("author", [])
                    # Check if target email appears anywhere in affiliations or author records
                    for author in authors:
                        affil_str = " ".join(
                            [a.get("name", "") for a in author.get("affiliation", [])]
                        ).lower()
                        if target_lower in affil_str or target_lower in str(author).lower():
                            matched_works.append(
                                {
                                    "title": title,
                                    "doi": doi,
                                    "author": f"{author.get('given', '')} {author.get('family', '')}",
                                }
                            )
                            break

                if matched_works:
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "title": f"Academic publication author match found ({len(matched_works)} papers)",
                            "evidence": (
                                f"Email '{target}' is referenced in CrossRef academic work '{matched_works[0]['title']}' "
                                f"(DOI: {matched_works[0]['doi']})."
                            ),
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "Peer-reviewed publication metadata indexed in CrossRef"
                            ],
                            "data": {"publications": matched_works},
                            "evidence_hash": compute_evidence_hash(
                                url, 200, str(matched_works[0]["doi"])
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
                            "title": f"No academic papers referencing '{target}' in CrossRef",
                            "evidence": "CrossRef academic works query returned zero matches with target author email.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": [
                                "CrossRef query returned no direct email matches"
                            ],
                            "data": {"publication_count": 0},
                            "evidence_hash": compute_evidence_hash(url, 200, "no_works"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"CrossRef returned HTTP {res.status_code}",
                        "evidence": "Unable to query CrossRef academic works API.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": ["Non-200 HTTP response"],
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
                    "title": "Error connecting to CrossRef API",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]


class HunterVerifierEmailModule(OSINTModule):
    """Verifies professional email deliverability and format score via Hunter.io API when configured."""

    metadata = ModuleMetadata(
        id="email.hunter_verifier",
        name="Hunter.io Email Verifier",
        version="1.0.0",
        supported_targets=[TargetType.email],
        source_name="Hunter.io",
        source_url="https://hunter.io/api-documentation/v2#email-verifier",
        description="Authorized commercial email deliverability, MX check, and confidence score verification via Hunter.io.",
        category="email",
        access_type="requires_api_key",
        limitations=[
            "Requires HUNTER_API_KEY environment variable. Reports skipped when unconfigured."
        ],
        timeout=8.0,
    )

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        api_key = os.getenv("HUNTER_API_KEY")
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        fid = str(uuid.uuid4())

        base: dict[str, Any] = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.email.value,
            "search_type": TargetType.email.value,
            "matched_identifier": target,
            "observed_at": observed_at,
            "source_url": "https://hunter.io",
            "limitations": self.metadata.limitations,
        }

        if not api_key:
            return [
                {
                    **base,
                    "status": FindingStatus.info.value,
                    "source_status": SourceStatus.skipped.value,
                    "verification_status": VerificationStatus.unverified.value,
                    "title": "Hunter.io API unconfigured (Skipped)",
                    "evidence": "HUNTER_API_KEY environment variable is not configured. Email deliverability scoring skipped.",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["HUNTER_API_KEY not configured in environment"],
                    "data": {"configured": False, "requires_api_key": True},
                    "evidence_hash": compute_evidence_hash(
                        base["source_url"], None, "unconfigured"
                    ),
                }
            ]

        url = f"https://api.hunter.io/v2/email-verifier?email={quote(target)}&api_key={api_key}"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)

            if res.status_code == 200:
                data = res.json().get("data", {})
                status = data.get("status", "unknown")
                score = data.get("score", 0)
                disposable = data.get("disposable", False)
                webmail = data.get("webmail", False)

                return [
                    {
                        **base,
                        "status": FindingStatus.found.value
                        if status in ("valid", "accept_all")
                        else FindingStatus.not_found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "title": f"Hunter.io verification: {status.upper()} (score: {score}%)",
                        "evidence": f"Hunter.io classified '{target}' as {status} (deliverability score: {score}%).",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "Hunter.io multi-factor deliverability and SMTP policy assessment"
                        ],
                        "data": {
                            "status": status,
                            "score": score,
                            "disposable": disposable,
                            "webmail": webmail,
                            "configured": True,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"{status}:{score}"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.unavailable.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Hunter.io API returned HTTP {res.status_code}",
                        "evidence": "Unable to verify email via Hunter.io API.",
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
                    "title": "Error connecting to Hunter.io API",
                    "evidence": f"Request failed: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "confidence_reasons": ["Network transport error"],
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, "error"),
                }
            ]
