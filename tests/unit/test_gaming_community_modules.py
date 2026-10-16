"""Unit tests for gaming and community platform adapters (Chess.com, Lichess, Hacker News, Wikipedia)."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus
from opentrace.modules.usernames.gaming_community import (
    ChessComUsernameModule,
    HackerNewsUsernameModule,
    LichessUsernameModule,
    WikipediaUserModule,
)


@pytest.mark.asyncio
@respx.mock
async def test_chesscom_found() -> None:
    mod = ChessComUsernameModule()
    respx.get("https://api.chess.com/pub/player/hikaru").mock(
        return_value=httpx.Response(
            200,
            json={
                "username": "hikaru",
                "player_id": 15448422,
                "title": "GM",
                "status": "premium",
                "joined": 1391212800,
            },
        )
    )

    findings = await mod.run("hikaru")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "Hikaru" in findings[0]["title"] or "hikaru" in findings[0]["title"]


@pytest.mark.asyncio
@respx.mock
async def test_chesscom_not_found() -> None:
    mod = ChessComUsernameModule()
    respx.get("https://api.chess.com/pub/player/unknownchessplayer999").mock(
        return_value=httpx.Response(404, json={"code": 0, "message": "User not found"})
    )

    findings = await mod.run("unknownchessplayer999")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_lichess_found() -> None:
    mod = LichessUsernameModule()
    respx.get("https://lichess.org/api/user/magnuscarlsen").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "magnuscarlsen",
                "username": "MagnusCarlsen",
                "createdAt": 1500000000000,
                "profile": {"bio": "World Champion"},
            },
        )
    )

    findings = await mod.run("magnuscarlsen")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_hackernews_found() -> None:
    mod = HackerNewsUsernameModule()
    respx.get("https://hacker-news.firebaseio.com/v0/user/pg.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "pg",
                "created": 1171825127,
                "karma": 150000,
                "about": "Founder of Y Combinator",
            },
        )
    )

    findings = await mod.run("pg")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_hackernews_not_found() -> None:
    mod = HackerNewsUsernameModule()
    respx.get("https://hacker-news.firebaseio.com/v0/user/nonexistenthnuser.json").mock(
        return_value=httpx.Response(200, text="null")
    )

    findings = await mod.run("nonexistenthnuser")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_wikipedia_user_found() -> None:
    mod = WikipediaUserModule()
    respx.get(url__startswith="https://en.wikipedia.org/w/api.php").mock(
        return_value=httpx.Response(
            200,
            json={
                "query": {
                    "users": [
                        {
                            "name": "Jimbo Wales",
                            "userid": 1,
                            "editcount": 10000,
                            "registration": "2001-01-15T00:00:00Z",
                        }
                    ]
                }
            },
        )
    )

    findings = await mod.run("Jimbo Wales")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
