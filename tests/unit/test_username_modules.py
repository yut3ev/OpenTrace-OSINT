"""Unit tests for GitHub and GitLab username modules using mocked HTTP responses."""

import pytest
import respx
from httpx import Response

from opentrace.modules.usernames.github import GitHubUsernameModule
from opentrace.modules.usernames.gitlab import GitLabUsernameModule


@pytest.mark.asyncio
@respx.mock
async def test_github_found():
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=Response(
            200,
            json={
                "login": "octocat",
                "name": "The Octocat",
                "bio": "GitHub mascot",
                "public_repos": 8,
                "created_at": "2011-01-25T18:44:36Z",
                "html_url": "https://github.com/octocat",
            },
        )
    )

    mod = GitHubUsernameModule()
    findings = await mod.run("octocat")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "found"
    assert f["confidence"] == "medium"
    assert f["data"]["login"] == "octocat"
    assert "octocat" in f["title"]


@pytest.mark.asyncio
@respx.mock
async def test_github_not_found():
    respx.get("https://api.github.com/users/nonexistentuser999").mock(
        return_value=Response(404, json={"message": "Not Found"})
    )

    mod = GitHubUsernameModule()
    findings = await mod.run("nonexistentuser999")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "not_found"
    assert f["confidence"] == "medium"


@pytest.mark.asyncio
@respx.mock
async def test_github_rate_limited():
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=Response(429, json={"message": "API rate limit exceeded"})
    )

    mod = GitHubUsernameModule()
    findings = await mod.run("octocat")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "unknown"  # Conservative: rate limited is unknown
    assert f["confidence"] == "none"


@pytest.mark.asyncio
@respx.mock
async def test_github_server_error():
    respx.get("https://api.github.com/users/octocat").mock(
        return_value=Response(500, text="Internal Server Error")
    )

    mod = GitHubUsernameModule()
    findings = await mod.run("octocat")
    assert len(findings) == 1
    assert findings[0]["status"] == "unknown"


@pytest.mark.asyncio
@respx.mock
async def test_gitlab_found():
    respx.get("https://gitlab.com/api/v4/users?username=johndoe").mock(
        return_value=Response(
            200,
            json=[
                {
                    "id": 12345,
                    "username": "johndoe",
                    "name": "John Doe",
                    "state": "active",
                    "web_url": "https://gitlab.com/johndoe",
                }
            ],
        )
    )

    mod = GitLabUsernameModule()
    findings = await mod.run("johndoe")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "found"
    assert f["confidence"] == "medium"
    assert f["data"]["username"] == "johndoe"


@pytest.mark.asyncio
@respx.mock
async def test_gitlab_not_found():
    respx.get("https://gitlab.com/api/v4/users?username=ghostuser").mock(
        return_value=Response(200, json=[])
    )

    mod = GitLabUsernameModule()
    findings = await mod.run("ghostuser")
    assert len(findings) == 1
    assert findings[0]["status"] == "not_found"
