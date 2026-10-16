"""Social, microblogging & bio link username adapters: Mastodon, Bluesky, Reddit, Telegram, Keybase, Linktree, Medium, Substack."""

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


class MastodonUsernameModule(OSINTModule):
    """Checks public Mastodon accounts on the flagship mastodon.social instance."""

    _metadata = ModuleMetadata(
        id="username.mastodon",
        name="Mastodon (social)",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Mastodon",
        source_url="https://mastodon.social/@{username}",
        description="Queries public Mastodon accounts via the official ActivityPub lookup API.",
        category="social",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Checks the primary mastodon.social server instance."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://mastodon.social/api/v1/accounts/lookup?acct={target}"
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
            "source_url": f"https://mastodon.social/@{target}",
            "profile_url": f"https://mastodon.social/@{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                display_name = data.get("display_name") or target
                profile_url = data.get("url") or f"https://mastodon.social/@{target}"
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": display_name,
                        "profile_url": profile_url,
                        "title": f"Mastodon user '{target}' found",
                        "evidence": f"Confirmed public Mastodon account at {profile_url}. Display name: {display_name}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "HTTP 200 from Mastodon account lookup API",
                            "Valid account ID and profile URL returned",
                        ],
                        "data": {
                            "id": data.get("id"),
                            "acct": data.get("acct"),
                            "followers_count": data.get("followers_count"),
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"mastodon:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Mastodon user '{target}' not found",
                        "evidence": f"Mastodon lookup returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Mastodon API"],
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
                        "title": f"Mastodon check returned status {res.status_code}",
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
                    "title": f"Mastodon check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class BlueskyUsernameModule(OSINTModule):
    """Checks public Bluesky handles on the AT Protocol public directory."""

    _metadata = ModuleMetadata(
        id="username.bluesky",
        name="Bluesky",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Bluesky",
        source_url="https://bsky.app/profile/{username}.bsky.social",
        description="Queries public AT Protocol profile information on Bluesky.",
        category="social",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Checks the primary .bsky.social handle suffix."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        handle = f"{target}.bsky.social"
        url = f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={handle}"
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
            "source_url": f"https://bsky.app/profile/{handle}",
            "profile_url": f"https://bsky.app/profile/{handle}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                display_name = data.get("displayName") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": display_name,
                        "title": f"Bluesky user '{target}' found",
                        "evidence": f"Confirmed public Bluesky account for @{handle}. Display name: {display_name}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "HTTP 200 and DID record returned from Bluesky public API"
                        ],
                        "data": {
                            "did": data.get("did"),
                            "handle": data.get("handle"),
                            "displayName": display_name,
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"bluesky:{target}"),
                    }
                ]
            elif res.status_code in (400, 404):
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Bluesky user '{target}' not found",
                        "evidence": f"Bluesky API confirmed handle @{handle} does not exist.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["AT Protocol resolver indicated actor not found"],
                        "data": {"status_code": res.status_code},
                        "evidence_hash": compute_evidence_hash(url, res.status_code, "not_found"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Bluesky returned status {res.status_code}",
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
                    "title": f"Bluesky check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class RedditUsernameModule(OSINTModule):
    """Checks public Reddit user profile existence via about.json."""

    _metadata = ModuleMetadata(
        id="username.reddit",
        name="Reddit",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Reddit",
        source_url="https://www.reddit.com/user/{username}",
        description="Queries public Reddit user karma, account creation date, and status.",
        category="social",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Strict User-Agent check and rate limiting apply."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://www.reddit.com/user/{target}/about.json"
        headers = {
            "User-Agent": f"{settings.user_agent} (OSINT verification)",
            "Accept": "application/json",
        }
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
            "source_url": f"https://www.reddit.com/user/{target}",
            "profile_url": f"https://www.reddit.com/user/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json().get("data", {})
                if data.get("name") and not data.get("is_suspended"):
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": data.get("name"),
                            "title": f"Reddit user 'u/{target}' found",
                            "evidence": f"Confirmed active public Reddit user at https://www.reddit.com/user/{target}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "HTTP 200 and valid Reddit user data schema returned"
                            ],
                            "data": {
                                "name": data.get("name"),
                                "total_karma": data.get("total_karma"),
                                "created_utc": data.get("created_utc"),
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, f"reddit:{target}"),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"Reddit user 'u/{target}' suspended or missing",
                            "evidence": "Reddit user is suspended or unavailable.",
                            "confidence": Confidence.medium.value,
                            "data": {"status_code": 200, "is_suspended": True},
                            "evidence_hash": compute_evidence_hash(url, 200, "suspended"),
                        }
                    ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Reddit user 'u/{target}' not found",
                        "evidence": f"Reddit returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Reddit about.json"],
                        "data": {"status_code": 404},
                        "evidence_hash": compute_evidence_hash(url, 404, "not_found"),
                    }
                ]
            elif res.status_code == 429:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.rate_limited.value,
                        "title": f"Reddit check rate limited for 'u/{target}'",
                        "evidence": "Reddit returned HTTP 429 Too Many Requests.",
                        "confidence": Confidence.none.value,
                        "data": {"status_code": 429},
                        "evidence_hash": compute_evidence_hash(url, 429, "rate_limited"),
                    }
                ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Reddit returned status {res.status_code}",
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
                    "title": f"Reddit check failed for 'u/{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class KeybaseUsernameModule(OSINTModule):
    """Checks public cryptographic identity profiles on Keybase."""

    _metadata = ModuleMetadata(
        id="username.keybase",
        name="Keybase",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Keybase",
        source_url="https://keybase.io/{username}",
        description="Queries public cryptographic proofs, identities, and PGP keys on Keybase.",
        category="social",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Public cryptographic proofs only."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={target}"
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
            "source_url": f"https://keybase.io/{target}",
            "profile_url": f"https://keybase.io/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                them = body.get("them", [])
                if them and len(them) > 0 and them[0] is not None:
                    user_obj = them[0]
                    profile = user_obj.get("profile", {})
                    d_name = profile.get("full_name") or target
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": d_name,
                            "title": f"Keybase profile '{target}' found",
                            "evidence": f"Confirmed public Keybase user at https://keybase.io/{target}. Full name: {d_name}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "HTTP 200 and verified Keybase cryptographic identity returned"
                            ],
                            "data": {
                                "id": user_obj.get("id"),
                                "full_name": d_name,
                                "bio": profile.get("bio"),
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, f"keybase:{target}"),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"Keybase user '{target}' not found",
                            "evidence": f"Keybase API returned empty user record for '{target}'.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["Keybase user directory lookup returned null"],
                            "data": {"result_empty": True},
                            "evidence_hash": compute_evidence_hash(url, 200, "not_found"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Keybase returned status {res.status_code}",
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
                    "title": f"Keybase check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
