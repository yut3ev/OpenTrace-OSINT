"""Gaming and online community platform username adapters: Chess.com, Lichess, Hacker News, Wikipedia."""

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


class ChessComUsernameModule(OSINTModule):
    """Checks Chess.com public player statistics via official published API."""

    _metadata = ModuleMetadata(
        id="username.chess_com",
        name="Chess.com",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Chess.com",
        source_url="https://www.chess.com/member/{username}",
        description="Queries official public Chess.com player ratings and profile.",
        category="gaming",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["API rate limit is 1 req/sec; accounts may be closed."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://api.chess.com/pub/player/{target}"
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
            "source_url": f"https://www.chess.com/member/{target}",
            "profile_url": f"https://www.chess.com/member/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                d_name = data.get("name") or data.get("username") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": d_name,
                        "title": f"Chess.com player '{target}' found",
                        "evidence": f"Confirmed public Chess.com account at https://www.chess.com/member/{target}. Status: {data.get('status')}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": [
                            "HTTP 200 from official Chess.com published player API"
                        ],
                        "data": {
                            "player_id": data.get("player_id"),
                            "status": data.get("status"),
                            "joined": data.get("joined"),
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"chess:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Chess.com player '{target}' not found",
                        "evidence": f"Chess.com API returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Chess.com player API"],
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
                        "title": f"Chess.com returned status {res.status_code}",
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
                    "title": f"Chess.com check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class LichessUsernameModule(OSINTModule):
    """Checks Lichess open chess player profile existence."""

    _metadata = ModuleMetadata(
        id="username.lichess",
        name="Lichess",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Lichess",
        source_url="https://lichess.org/@/{username}",
        description="Queries open-source Lichess player profile and game statistics.",
        category="gaming",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Closed accounts will return disabled status."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://lichess.org/api/user/{target}"
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
            "source_url": f"https://lichess.org/@/{target}",
            "profile_url": f"https://lichess.org/@/{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                profile_info = data.get("profile", {})
                d_name = profile_info.get("realName") or data.get("username") or target
                return [
                    {
                        **base,
                        "status": FindingStatus.found.value,
                        "source_status": SourceStatus.succeeded.value,
                        "verification_status": VerificationStatus.verified.value,
                        "display_name": d_name,
                        "title": f"Lichess player '{target}' found",
                        "evidence": f"Confirmed public Lichess account at https://lichess.org/@/{target}.",
                        "confidence": Confidence.high.value,
                        "confidence_reasons": ["HTTP 200 returned from Lichess user API"],
                        "data": {
                            "id": data.get("id"),
                            "username": data.get("username"),
                            "games": data.get("count", {}).get("all"),
                        },
                        "evidence_hash": compute_evidence_hash(url, 200, f"lichess:{target}"),
                    }
                ]
            elif res.status_code == 404:
                return [
                    {
                        **base,
                        "status": FindingStatus.not_found.value,
                        "source_status": SourceStatus.no_match.value,
                        "verification_status": VerificationStatus.unverified.value,
                        "title": f"Lichess player '{target}' not found",
                        "evidence": f"Lichess API returned 404 Not Found at {url}.",
                        "confidence": Confidence.medium.value,
                        "confidence_reasons": ["HTTP 404 from Lichess API"],
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
                        "title": f"Lichess returned status {res.status_code}",
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
                    "title": f"Lichess check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class HackerNewsUsernameModule(OSINTModule):
    """Checks Hacker News public user karma and age via Firebase API."""

    _metadata = ModuleMetadata(
        id="username.hackernews",
        name="Hacker News",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Hacker News",
        source_url="https://news.ycombinator.com/user?id={username}",
        description="Queries public Hacker News user karma, creation date, and about text.",
        category="community",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Returns null JSON when account does not exist."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://hacker-news.firebaseio.com/v0/user/{target}.json"
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
            "source_url": f"https://news.ycombinator.com/user?id={target}",
            "profile_url": f"https://news.ycombinator.com/user?id={target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                if body and isinstance(body, dict) and body.get("id"):
                    return [
                        {
                            **base,
                            "status": FindingStatus.found.value,
                            "source_status": SourceStatus.succeeded.value,
                            "verification_status": VerificationStatus.verified.value,
                            "display_name": body.get("id"),
                            "title": f"Hacker News user '{target}' found",
                            "evidence": f"Confirmed public Hacker News account at https://news.ycombinator.com/user?id={target}. Karma: {body.get('karma')}.",
                            "confidence": Confidence.high.value,
                            "confidence_reasons": [
                                "HTTP 200 and valid user record returned from Hacker News Firebase API"
                            ],
                            "data": {
                                "id": body.get("id"),
                                "karma": body.get("karma"),
                                "created": body.get("created"),
                            },
                            "evidence_hash": compute_evidence_hash(url, 200, f"hn:{target}"),
                        }
                    ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"Hacker News user '{target}' not found",
                            "evidence": f"Hacker News API returned null user record for '{target}'.",
                            "confidence": Confidence.medium.value,
                            "confidence_reasons": ["Null JSON response for requested user ID"],
                            "data": {"body": None},
                            "evidence_hash": compute_evidence_hash(url, 200, "null"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Hacker News returned status {res.status_code}",
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
                    "title": f"Hacker News check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]


class WikipediaUserModule(OSINTModule):
    """Checks Wikipedia editor user registration via official MediaWiki API."""

    _metadata = ModuleMetadata(
        id="username.wikipedia",
        name="Wikipedia User",
        version="0.1.0",
        supported_targets=[TargetType.username],
        source_name="Wikipedia",
        source_url="https://en.wikipedia.org/wiki/User:{username}",
        description="Queries Wikipedia registered editor profiles and edit counts via MediaWiki API.",
        category="community",
        access_type="public_api",
        enabled=True,
        implementation_status="implemented",
        limitations=["Checks en.wikipedia.org editor directory."],
    )

    @property
    def metadata(self) -> ModuleMetadata:
        return self._metadata

    async def run(self, target: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        inv_id = (context or {}).get("investigation_id", "")
        observed_at = datetime.now(UTC)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=users&ususers={target}&usprop=registration|editcount&format=json"
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
            "source_url": f"https://en.wikipedia.org/wiki/User:{target}",
            "profile_url": f"https://en.wikipedia.org/wiki/User:{target}",
            "limitations": self.metadata.limitations,
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.metadata.timeout, connect=5.0)
            ) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                body = res.json()
                users = body.get("query", {}).get("users", [])
                if users and len(users) > 0:
                    u = users[0]
                    if "missing" not in u and u.get("userid"):
                        return [
                            {
                                **base,
                                "status": FindingStatus.found.value,
                                "source_status": SourceStatus.succeeded.value,
                                "verification_status": VerificationStatus.verified.value,
                                "display_name": u.get("name"),
                                "title": f"Wikipedia editor '{target}' found",
                                "evidence": f"Confirmed registered Wikipedia user account at https://en.wikipedia.org/wiki/User:{target}. Edit count: {u.get('editcount')}.",
                                "confidence": Confidence.high.value,
                                "confidence_reasons": [
                                    "Valid user ID and registration details returned from MediaWiki API"
                                ],
                                "data": {
                                    "userid": u.get("userid"),
                                    "editcount": u.get("editcount"),
                                    "registration": u.get("registration"),
                                },
                                "evidence_hash": compute_evidence_hash(url, 200, f"wiki:{target}"),
                            }
                        ]
                    else:
                        return [
                            {
                                **base,
                                "status": FindingStatus.not_found.value,
                                "source_status": SourceStatus.no_match.value,
                                "verification_status": VerificationStatus.unverified.value,
                                "title": f"Wikipedia editor '{target}' not found",
                                "evidence": f"MediaWiki API reported user '{target}' does not exist.",
                                "confidence": Confidence.medium.value,
                                "confidence_reasons": ["MediaWiki API flagged user as missing"],
                                "data": {"missing": True},
                                "evidence_hash": compute_evidence_hash(url, 200, "missing"),
                            }
                        ]
                else:
                    return [
                        {
                            **base,
                            "status": FindingStatus.not_found.value,
                            "source_status": SourceStatus.no_match.value,
                            "verification_status": VerificationStatus.unverified.value,
                            "title": f"Wikipedia user '{target}' not found",
                            "evidence": "No user list returned by MediaWiki query.",
                            "confidence": Confidence.low.value,
                            "data": {"status_code": 200},
                            "evidence_hash": compute_evidence_hash(url, 200, "empty"),
                        }
                    ]
            else:
                return [
                    {
                        **base,
                        "status": FindingStatus.unknown.value,
                        "source_status": SourceStatus.error.value,
                        "title": f"Wikipedia API returned status {res.status_code}",
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
                    "title": f"Wikipedia check failed for '{target}'",
                    "evidence": f"Network error: {type(exc).__name__}: {str(exc)}",
                    "confidence": Confidence.none.value,
                    "data": {"error": str(exc)},
                    "evidence_hash": compute_evidence_hash(url, None, f"error:{exc}"),
                }
            ]
