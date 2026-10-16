"""Unit tests for people and biographical search modules (Wikipedia, DBLP, OpenAlex)."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus
from opentrace.modules.people.dblp import DblpAuthorModule
from opentrace.modules.people.openalex import OpenAlexAuthorModule
from opentrace.modules.people.wikipedia import WikipediaPersonModule


@pytest.mark.asyncio
@respx.mock
async def test_wikipedia_person_found() -> None:
    mod = WikipediaPersonModule()
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=httpx.Response(
            200,
            json={
                "query": {
                    "search": [
                        {
                            "title": "Alan Turing",
                            "pageid": 1234,
                            "snippet": "Alan Mathison Turing was an English mathematician and computer scientist...",
                            "timestamp": "2023-01-01T00:00:00Z",
                        }
                    ]
                }
            },
        )
    )

    findings = await mod.run("Alan Turing")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "Alan Turing" in findings[0]["title"]
    assert findings[0]["verification_status"] == "candidate"


@pytest.mark.asyncio
@respx.mock
async def test_wikipedia_person_not_found() -> None:
    mod = WikipediaPersonModule()
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=httpx.Response(200, json={"query": {"search": []}})
    )

    findings = await mod.run("Nonexistent Person Xyz123")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_dblp_author_found() -> None:
    mod = DblpAuthorModule()
    respx.get("https://dblp.org/search/author/api").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "hits": {
                        "@total": "1",
                        "hit": [
                            {
                                "info": {
                                    "author": "Claude E. Shannon",
                                    "url": "https://dblp.org/pid/s/ClaudeEShannon.html",
                                }
                            }
                        ],
                    }
                }
            },
        )
    )

    findings = await mod.run("Claude Shannon")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "Claude E. Shannon" in findings[0]["title"]


@pytest.mark.asyncio
@respx.mock
async def test_openalex_author_found() -> None:
    mod = OpenAlexAuthorModule()
    respx.get("https://api.openalex.org/authors").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/A12345678",
                        "display_name": "Tim Berners-Lee",
                        "works_count": 120,
                        "cited_by_count": 45000,
                        "last_known_institution": {
                            "display_name": "Massachusetts Institute of Technology",
                            "country_code": "US",
                        },
                    }
                ]
            },
        )
    )

    findings = await mod.run("Tim Berners-Lee")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "Tim Berners-Lee" in findings[0]["title"]
