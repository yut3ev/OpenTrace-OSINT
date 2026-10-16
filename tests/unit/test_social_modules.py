"""Unit tests for social platform adapters (Mastodon, Bluesky, Reddit, Keybase)."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus
from opentrace.modules.usernames.social import (
    BlueskyUsernameModule,
    KeybaseUsernameModule,
    MastodonUsernameModule,
    RedditUsernameModule,
)


@pytest.mark.asyncio
@respx.mock
async def test_mastodon_found() -> None:
    mod = MastodonUsernameModule()
    respx.get("https://mastodon.social/api/v1/accounts/lookup?acct=gargron").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "1",
                "username": "Gargron",
                "display_name": "Eugen Rochko",
                "url": "https://mastodon.social/@Gargron",
                "statuses_count": 500,
            },
        )
    )

    findings = await mod.run("gargron")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["display_name"] == "Eugen Rochko"


@pytest.mark.asyncio
@respx.mock
async def test_mastodon_not_found() -> None:
    mod = MastodonUsernameModule()
    respx.get("https://mastodon.social/api/v1/accounts/lookup?acct=nonexistent999").mock(
        return_value=httpx.Response(404, json={"error": "Record not found"})
    )

    findings = await mod.run("nonexistent999")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_bluesky_found() -> None:
    mod = BlueskyUsernameModule()
    respx.get(
        "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=jay.bsky.social"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "handle": "jay.bsky.social",
                "displayName": "Jay Graber",
                "description": "CEO at Bluesky",
            },
        )
    )

    findings = await mod.run("jay")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_bluesky_not_found() -> None:
    mod = BlueskyUsernameModule()
    respx.get(
        "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor=unknownbskyuser.bsky.social"
    ).mock(return_value=httpx.Response(400, json={"error": "ProfileNotFound"}))

    findings = await mod.run("unknownbskyuser")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_reddit_found() -> None:
    mod = RedditUsernameModule()
    respx.get("https://www.reddit.com/user/spez/about.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "name": "spez",
                    "id": "1w72",
                    "created_utc": 1118000000,
                    "total_karma": 50000,
                }
            },
        )
    )

    findings = await mod.run("spez")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_reddit_not_found() -> None:
    mod = RedditUsernameModule()
    respx.get("https://www.reddit.com/user/nonexistentreddituser123/about.json").mock(
        return_value=httpx.Response(404, json={"message": "Not Found", "error": 404})
    )

    findings = await mod.run("nonexistentreddituser123")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_keybase_found() -> None:
    mod = KeybaseUsernameModule()
    respx.get("https://keybase.io/_/api/1.0/user/lookup.json?usernames=max").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": {"code": 0, "name": "OK"},
                "them": [{"id": "abc123", "basics": {"username": "max"}}],
            },
        )
    )

    findings = await mod.run("max")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
