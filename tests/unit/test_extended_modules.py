"""Unit tests with mocked fixtures for all extended OSINT modules."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus, SourceStatus
from opentrace.modules.email.extended_email import (
    GitHubCommitsEmailModule,
    PgpKeyserverEmailModule,
)
from opentrace.modules.people.extended_people import (
    ArxivAuthorModule,
    SearchQueryGeneratorModule,
)
from opentrace.modules.phone.extended_phone import (
    PhoneCarrierPrefixModule,
    PhoneInternationalModule,
)
from opentrace.modules.usernames.extended_dev import (
    CodebergUsernameModule,
    CratesIoUsernameModule,
    PackagistUsernameModule,
)
from opentrace.modules.usernames.extended_gaming import (
    CodeforcesUsernameModule,
    DuolingoUsernameModule,
    TryHackMeUsernameModule,
)
from opentrace.modules.usernames.extended_social import (
    BuyMeACoffeeUsernameModule,
    MediumUsernameModule,
    SubstackUsernameModule,
)

# ==============================================================================
# DEVELOPER MODULE TESTS
# ==============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_codeberg_username_found() -> None:
    respx.get("https://codeberg.org/api/v1/users/coder123").mock(
        return_value=httpx.Response(200, json={"id": 42, "username": "coder123", "name": "Coder"})
    )
    mod = CodebergUsernameModule()
    findings = await mod.run("coder123")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["source_status"] == SourceStatus.succeeded.value


@pytest.mark.asyncio
@respx.mock
async def test_codeberg_username_not_found() -> None:
    respx.get("https://codeberg.org/api/v1/users/nobody").mock(return_value=httpx.Response(404))
    mod = CodebergUsernameModule()
    findings = await mod.run("nobody")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_packagist_username_found() -> None:
    respx.get("https://packagist.org/packages/list.json?vendor=symfony").mock(
        return_value=httpx.Response(
            200, json={"packageNames": ["symfony/console", "symfony/http-foundation"]}
        )
    )
    mod = PackagistUsernameModule()
    findings = await mod.run("symfony")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["package_count"] == 2


@pytest.mark.asyncio
@respx.mock
async def test_cratesio_username_found() -> None:
    respx.get("https://crates.io/api/v1/users/alexcrichton").mock(
        return_value=httpx.Response(
            200, json={"user": {"id": 1, "login": "alexcrichton", "name": "Alex"}}
        )
    )
    mod = CratesIoUsernameModule()
    findings = await mod.run("alexcrichton")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


# ==============================================================================
# SOCIAL & CREATOR MODULE TESTS
# ==============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_medium_username_found() -> None:
    respx.get("https://medium.com/@author").mock(
        return_value=httpx.Response(200, text="<html><body><h1>Author Stories</h1></body></html>")
    )
    mod = MediumUsernameModule()
    findings = await mod.run("author")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_medium_username_soft_404() -> None:
    respx.get("https://medium.com/@nonexistent").mock(
        return_value=httpx.Response(
            200, text="<html><body>Out of nothing, something. PAGE NOT FOUND</body></html>"
        )
    )
    mod = MediumUsernameModule()
    findings = await mod.run("nonexistent")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_substack_username_found() -> None:
    respx.get("https://techinsider.substack.com").mock(
        return_value=httpx.Response(
            200, text="<html><body>Welcome to Tech Insider Newsletter</body></html>"
        )
    )
    mod = SubstackUsernameModule()
    findings = await mod.run("techinsider")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_buymeacoffee_username_found() -> None:
    respx.get("https://www.buymeacoffee.com/creator").mock(
        return_value=httpx.Response(200, text="<html><body>Buy Creator a coffee!</body></html>")
    )
    mod = BuyMeACoffeeUsernameModule()
    findings = await mod.run("creator")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


# ==============================================================================
# GAMING & SECURITY MODULE TESTS
# ==============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_duolingo_username_found() -> None:
    respx.get("https://www.duolingo.com/2017-06-30/users?username=polyglot").mock(
        return_value=httpx.Response(
            200,
            json={
                "users": [
                    {
                        "username": "polyglot",
                        "name": "Poly Glot",
                        "streak": 365,
                        "totalXp": 50000,
                        "courses": [{"title": "Spanish"}, {"title": "French"}],
                    }
                ]
            },
        )
    )
    mod = DuolingoUsernameModule()
    findings = await mod.run("polyglot")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["streak"] == 365


@pytest.mark.asyncio
@respx.mock
async def test_codeforces_username_found() -> None:
    respx.get("https://codeforces.com/api/user.info?handles=tourist").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "result": [
                    {
                        "handle": "tourist",
                        "rating": 3800,
                        "rank": "legendary grandmaster",
                        "maxRating": 3979,
                    }
                ],
            },
        )
    )
    mod = CodeforcesUsernameModule()
    findings = await mod.run("tourist")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["rating"] == 3800


@pytest.mark.asyncio
@respx.mock
async def test_tryhackme_username_found() -> None:
    respx.get("https://tryhackme.com/api/user/exist/hacker").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    mod = TryHackMeUsernameModule()
    findings = await mod.run("hacker")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


# ==============================================================================
# EMAIL EXTENDED TESTS
# ==============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_github_commits_email_found() -> None:
    respx.get("https://api.github.com/search/commits?q=author-email:octocat%40github.com").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_count": 5,
                "items": [
                    {
                        "sha": "1234567890abcdef",
                        "commit": {
                            "author": {"name": "The Octocat", "email": "octocat@github.com"}
                        },
                        "repository": {
                            "full_name": "octocat/Hello-World",
                            "html_url": "https://github.com/octocat/Hello-World",
                        },
                    }
                ],
            },
        )
    )
    mod = GitHubCommitsEmailModule()
    findings = await mod.run("octocat@github.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["commit_count"] == 5


@pytest.mark.asyncio
@respx.mock
async def test_pgp_keyserver_found() -> None:
    respx.get("https://keys.openpgp.org/vks/v1/by-email/sec%40example.com").mock(
        return_value=httpx.Response(
            200,
            text="-----BEGIN PGP PUBLIC KEY BLOCK-----\nmQENBF6...==abcd\n-----END PGP PUBLIC KEY BLOCK-----",
        )
    )
    mod = PgpKeyserverEmailModule()
    findings = await mod.run("sec@example.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["has_pgp_key"] is True


# ==============================================================================
# PHONE EXTENDED TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_phone_international_module() -> None:
    mod = PhoneInternationalModule()
    findings = await mod.run("+14155552671")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["data"]["e164"] == "+14155552671"
    assert findings[0]["data"]["country_code"] == 1


@pytest.mark.asyncio
async def test_phone_carrier_prefix_module() -> None:
    mod = PhoneCarrierPrefixModule()
    findings = await mod.run("+14155552671")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


# ==============================================================================
# PEOPLE EXTENDED TESTS
# ==============================================================================


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_author_found() -> None:
    respx.get("https://export.arxiv.org/api/query?search_query=au:Turing&max_results=3").mock(
        return_value=httpx.Response(
            200,
            text="<feed><entry><title>On Computable Numbers</title></entry></feed>",
        )
    )
    mod = ArxivAuthorModule()
    findings = await mod.run("Turing")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "On Computable Numbers" in findings[0]["data"]["sample_paper"]


@pytest.mark.asyncio
async def test_search_query_generator_module() -> None:
    mod = SearchQueryGeneratorModule()
    findings = await mod.run("Grace Hopper")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "duckduckgo_url" in findings[0]["data"]
    assert "google_url" in findings[0]["data"]
    assert "linkedin_search_url" in findings[0]["data"]
