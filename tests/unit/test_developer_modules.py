"""Unit tests for developer platform username adapters (Bitbucket, Docker Hub, PyPI, NPM, HuggingFace, Dev.to)."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus, SourceStatus
from opentrace.modules.usernames.developer import (
    BitbucketUsernameModule,
    DevToUsernameModule,
    DockerHubUsernameModule,
    HuggingFaceUsernameModule,
    NpmUsernameModule,
    PyPIUsernameModule,
)


@pytest.mark.asyncio
@respx.mock
async def test_bitbucket_found() -> None:
    mod = BitbucketUsernameModule()
    respx.get("https://api.bitbucket.org/2.0/users/sampleuser").mock(
        return_value=httpx.Response(
            200,
            json={
                "username": "sampleuser",
                "display_name": "Sample Developer",
                "created_on": "2020-01-01T00:00:00Z",
                "links": {"html": {"href": "https://bitbucket.org/sampleuser/"}},
            },
        )
    )

    findings = await mod.run("sampleuser")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.found.value
    assert f["source_status"] == SourceStatus.succeeded.value
    assert f["data"]["display_name"] == "Sample Developer"


@pytest.mark.asyncio
@respx.mock
async def test_bitbucket_not_found() -> None:
    mod = BitbucketUsernameModule()
    respx.get("https://api.bitbucket.org/2.0/users/nonexistent").mock(
        return_value=httpx.Response(
            404, json={"type": "error", "error": {"message": "User not found"}}
        )
    )

    findings = await mod.run("nonexistent")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.not_found.value
    assert f["source_status"] == SourceStatus.no_match.value


@pytest.mark.asyncio
@respx.mock
async def test_dockerhub_found() -> None:
    mod = DockerHubUsernameModule()
    respx.get(url__startswith="https://hub.docker.com/v2/users/dockertest").mock(
        return_value=httpx.Response(
            200,
            json={
                "username": "dockertest",
                "full_name": "Docker Publisher",
                "date_joined": "2019-05-01T00:00:00Z",
                "profile_url": "https://hub.docker.com/u/dockertest",
            },
        )
    )

    findings = await mod.run("dockertest")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["source_status"] == SourceStatus.succeeded.value


@pytest.mark.asyncio
@respx.mock
async def test_dockerhub_not_found() -> None:
    mod = DockerHubUsernameModule()
    respx.get(url__startswith="https://hub.docker.com/v2/users/unknownuser").mock(
        return_value=httpx.Response(404)
    )

    findings = await mod.run("unknownuser")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value
    assert findings[0]["source_status"] == SourceStatus.no_match.value


@pytest.mark.asyncio
@respx.mock
async def test_pypi_found() -> None:
    mod = PyPIUsernameModule()
    respx.get("https://pypi.org/user/psf/").mock(
        return_value=httpx.Response(
            200,
            text="<html><body><h1>User psf</h1><p>12 packages released</p></body></html>",
        )
    )

    findings = await mod.run("psf")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_pypi_not_found() -> None:
    mod = PyPIUsernameModule()
    respx.get("https://pypi.org/user/invaliduser999/").mock(
        return_value=httpx.Response(404, text="Not Found")
    )

    findings = await mod.run("invaliduser999")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_npm_found() -> None:
    mod = NpmUsernameModule()
    respx.get("https://www.npmjs.com/~sindresorhus").mock(
        return_value=httpx.Response(
            200,
            text="<html><title>~sindresorhus - 250 packages on npm</title></html>",
        )
    )

    findings = await mod.run("sindresorhus")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_npm_not_found() -> None:
    mod = NpmUsernameModule()
    respx.get("https://www.npmjs.com/~nosuchpackageauthor").mock(return_value=httpx.Response(404))

    findings = await mod.run("nosuchpackageauthor")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
@respx.mock
async def test_huggingface_found() -> None:
    mod = HuggingFaceUsernameModule()
    respx.get("https://huggingface.co/api/users/google/overview").mock(
        return_value=httpx.Response(
            200,
            json={
                "fullname": "Google",
                "orgs": [],
                "numModels": 450,
            },
        )
    )

    findings = await mod.run("google")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value


@pytest.mark.asyncio
@respx.mock
async def test_devto_found() -> None:
    mod = DevToUsernameModule()
    respx.get("https://dev.to/api/users/by_username?url=thepracticaldev").mock(
        return_value=httpx.Response(
            200,
            json={
                "username": "thepracticaldev",
                "name": "The Practical Dev",
                "joined_at": "2016-01-01",
            },
        )
    )

    findings = await mod.run("thepracticaldev")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
