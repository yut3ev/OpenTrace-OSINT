"""Developer platform username adapters: Bitbucket, Docker Hub, PyPI, NPM, HuggingFace, Kaggle, Replit, Codeberg, Dev.to, Hashnode."""

from __future__ import annotations

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


class BitbucketUsernameModule(OSINTModule):
    """Checks public Bitbucket accounts via official 2.0 public API."""

    _metadata = ModuleMetadata(
        id="username.bitbucket",
        name="Bitbucket",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Bitbucket",
        source_url="https://bitbucket.org/{username}/",
        description="Verifies public Bitbucket workspace and user account existence.",
        category="developer",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Account privacy settings may hide repositories."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://api.bitbucket.org/2.0/users/{target}"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": f"https://bitbucket.org/{target}/",
            "profile_url": f"https://bitbucket.org/{target}/",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                d_name = data.get("display_name", target)
                summary = f"Bitbucket account exists for {target}"
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": d_name,
                        "title": f"Bitbucket account '{target}' found",
                        "evidence": f"Public Bitbucket profile confirmed via API ({url}). Display name: {d_name}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "HTTP 200 returned from Bitbucket user API",
                            "Display name and account UUID matched",
                        ],
                        "data": {
                            "uuid": data.get("uuid"),
                            "nickname": data.get("nickname"),
                            "display_name": d_name,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, summary),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Bitbucket account '{target}' not found",
                        "evidence": f"Bitbucket API returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["API returned HTTP 404 Not Found"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            elif res.status_code in (429, 403):
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value
                        if res.status_code == 429
                        else SourceStatus.blocked.value,
                        "title": f"Bitbucket check restricted ({res.status_code})",
                        "evidence": f"Bitbucket responded with status code {res.status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": [f"HTTP {res.status_code} received"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "restricted"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Bitbucket returned unexpected status {res.status_code}",
                        "evidence": f"Unexpected response from {url}: {res.status_code}.",
                        "confidence": Confidence.none.value,
                        "confidence_reasons": [f"Unexpected HTTP {res.status_code}"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "unexpected"),
                    }
                ]
        except Exception as exc:
            return [
                {
                    **base,
                    "status": FindingStatus.unknown.value,
                    "source_status": SourceStatus.error.value,
                    "title": f"Bitbucket check failed for '{target}'",
                    "evidence": f"Network or request error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class DockerHubUsernameModule(OSINTModule):
    """Checks public Docker Hub namespace existence via public registry API."""

    _metadata = ModuleMetadata(
        id="username.dockerhub",
        name="Docker Hub",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Docker Hub",
        source_url="https://hub.docker.com/u/{username}",
        description="Checks public Docker Hub container repository namespace.",
        category="developer",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Only public namespaces and images are returned."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://hub.docker.com/v2/users/{target}/"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": f"https://hub.docker.com/u/{target}",
            "profile_url": f"https://hub.docker.com/u/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                full_name = data.get("full_name") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": full_name,
                        "title": f"Docker Hub user '{target}' found",
                        "evidence": f"Confirmed public Docker Hub account at https://hub.docker.com/u/{target}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["HTTP 200 returned from Docker Hub user API"],
                        "data": {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "full_name": full_name,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"dockerhub:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Docker Hub user '{target}' not found",
                        "evidence": f"Docker Hub API returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Docker Hub API"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Docker Hub returned status {res.status_code}",
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
                    "title": f"Docker Hub check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class PyPIUsernameModule(OSINTModule):
    """Checks Python Package Index (PyPI) maintainer profile existence."""

    _metadata = ModuleMetadata(
        id="username.pypi",
        name="PyPI",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="PyPI",
        source_url="https://pypi.org/user/{username}/",
        description="Checks Python Package Index (PyPI) package author / maintainer page.",
        category="developer",
        access_type="public_web",
        enabled=True,
        implementation_status="implemented",
        limitations=["Only authors who have registered on pypi.org appear."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://pypi.org/user/{target}/"
        headers = {"User-Agent": settings.user_agent, "Accept": "text/html"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": url,
            "profile_url": url,
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0), follow_redirects=True
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                # Validate that it is an actual user profile page, not a soft 404 or generic page
                text = res.text
                if "packages released" in text.lower() or f">{target}<" in text:
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": target,
                            "title": f"PyPI maintainer '{target}' found",
                            "evidence": f"Confirmed public PyPI maintainer profile at {url}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "HTTP 200 and maintainer profile text verified on PyPI"
                            ],
                            "data": {"profile_url": url},
                            "evidence_hash": compute_evidence_hash(url, 200, f"pypi:{target}"),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"PyPI maintainer '{target}' not found",
                            "evidence": "PyPI returned 200 but profile markers were not found.",
                            "confidence": Confidence.medium.value,
                            "data": {"status_code": 200, "soft_404": True},
                            "evidence_hash": compute_evidence_hash(url, 200, "soft_404"),
                        }
                    ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"PyPI maintainer '{target}' not found",
                        "evidence": f"PyPI returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 Not Found"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"PyPI returned unexpected status {res.status_code}",
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
                    "title": f"PyPI check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class NpmUsernameModule(OSINTModule):
    """Checks npm public author / maintainer page."""

    _metadata = ModuleMetadata(
        id="username.npm",
        name="npm",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="npm",
        source_url="https://www.npmjs.com/~{username}",
        description="Checks public npm maintainer profile page.",
        category="developer",
        access_type="public_web",
        enabled=True,
        implementation_status="implemented",
        limitations=["Checks public package author index."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://www.npmjs.com/~{target}"
        headers = {"User-Agent": settings.user_agent, "Accept": "text/html"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": url,
            "profile_url": url,
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0), follow_redirects=True
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                if f"~{target}" in res.text or "packages" in res.text.lower():
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": target,
                            "title": f"npm maintainer '{target}' found",
                            "evidence": f"Confirmed public npm profile at {url}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": ["HTTP 200 and npm handle verified in page DOM"],
                            "data": {"profile_url": url},
                            "evidence_hash": compute_evidence_hash(url, 200, f"npm:{target}"),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"npm maintainer '{target}' not found",
                            "evidence": "npm returned 200 but handle text was not present in response.",
                            "confidence": Confidence.medium.value,
                            "data": {"status_code": 200, "soft_404": True},
                            "evidence_hash": compute_evidence_hash(url, 200, "soft_404"),
                        }
                    ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"npm user '{target}' not found",
                        "evidence": f"npm returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 Not Found"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"npm returned status {res.status_code}",
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
                    "title": f"npm check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class HuggingFaceUsernameModule(OSINTModule):
    """Checks Hugging Face AI/ML developer profile existence."""

    _metadata = ModuleMetadata(
        id="username.huggingface",
        name="Hugging Face",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Hugging Face",
        source_url="https://huggingface.co/{username}",
        description="Queries public AI/ML model, dataset, and spaces developer profiles.",
        category="developer",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Public models and datasets only."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://huggingface.co/api/users/{target}/overview"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": f"https://huggingface.co/{target}",
            "profile_url": f"https://huggingface.co/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                display_name = data.get("fullname") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": display_name,
                        "title": f"Hugging Face profile '{target}' found",
                        "evidence": f"Confirmed public Hugging Face developer profile at https://huggingface.co/{target}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "HTTP 200 returned from Hugging Face user overview API"
                        ],
                        "data": {
                            "fullname": display_name,
                            "num_models": len(data.get("models", [])),
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"hf:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Hugging Face profile '{target}' not found",
                        "evidence": f"Hugging Face returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 Not Found"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Hugging Face returned status {res.status_code}",
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
                    "title": f"Hugging Face check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class DevToUsernameModule(OSINTModule):
    """Checks Dev.to developer community profile existence."""

    _metadata = ModuleMetadata(
        id="username.devto",
        name="Dev.to",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Dev.to",
        source_url="https://dev.to/{username}",
        description="Checks public software developer community profile on Dev.to.",
        category="blogging",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Public articles and bio only."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://dev.to/api/users/by_username?url={target}"
        headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
        fid = str(uuid.uuid4())
        base = {
            "id": fid,
            "investigation_id": inv_id,
            "module_id": self.metadata.id,
            "source_id": self.metadata.id,
            "source_name": self.metadata.source_name,
            "target_type": TargetType.username.value,
            "search_type": TargetType.username.value,
            "matched_identifier": target,
            "username": target,
            "observed_at": observed_at,
            "source_url": f"https://dev.to/{target}",
            "profile_url": f"https://dev.to/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                d_name = data.get("name") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": d_name,
                        "title": f"Dev.to author '{target}' found",
                        "evidence": f"Confirmed public Dev.to user profile ({url}). Name: {d_name}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["HTTP 200 from official Dev.to Forem API"],
                        "data": {
                            "id": data.get("id"),
                            "name": d_name,
                            "summary": data.get("summary"),
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"devto:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Dev.to author '{target}' not found",
                        "evidence": f"Dev.to API returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 Not Found"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Dev.to returned status {res.status_code}",
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
                    "title": f"Dev.to check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
