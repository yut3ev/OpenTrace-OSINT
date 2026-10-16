"""Unit tests for authorized provider modules: email.hibp and phone.provider_api."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus, SourceStatus
from opentrace.config import Settings
from opentrace.modules.email.hibp import HaveIBeenPwnedEmailModule
from opentrace.modules.phone.provider import AuthorizedPhoneLookupModule


@pytest.mark.asyncio
async def test_hibp_unconfigured_skips() -> None:
    """When HIBP_API_KEY is not configured, the module should return a skipped finding."""
    module = HaveIBeenPwnedEmailModule(settings=Settings(hibp_api_key=None))
    findings = await module.run("user@example.com")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.info.value
    assert f["source_status"] == SourceStatus.skipped.value
    assert "not configured" in f["evidence"]


@pytest.mark.asyncio
@respx.mock
async def test_hibp_configured_breaches_found() -> None:
    """When HIBP_API_KEY is set and breaches exist, return verified finding with breach data."""
    respx.get(
        "https://haveibeenpwned.com/api/v3/breachedaccount/target%40example.com?truncateResponse=false"
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "Name": "Adobe",
                    "Title": "Adobe",
                    "Domain": "adobe.com",
                    "BreachDate": "2013-10-04",
                    "Description": "In October 2013, Adobe was breached.",
                    "DataClasses": ["Email addresses", "Passwords", "Usernames"],
                }
            ],
        )
    )

    module = HaveIBeenPwnedEmailModule(settings=Settings(hibp_api_key="mock-key-123"))
    findings = await module.run("target@example.com")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.found.value
    assert f["source_status"] == SourceStatus.succeeded.value
    assert f["confidence"] == "high"
    assert f["data"]["breach_count"] == 1
    assert "Adobe" in f["data"]["breaches"]


@pytest.mark.asyncio
@respx.mock
async def test_hibp_no_breach_returns_no_match() -> None:
    """404 on HIBP means no breaches found."""
    respx.get(
        "https://haveibeenpwned.com/api/v3/breachedaccount/clean%40example.com?truncateResponse=false"
    ).mock(return_value=httpx.Response(404))

    module = HaveIBeenPwnedEmailModule(settings=Settings(hibp_api_key="mock-key-123"))
    findings = await module.run("clean@example.com")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.not_found.value
    assert f["source_status"] == SourceStatus.no_match.value


@pytest.mark.asyncio
async def test_phone_provider_unconfigured_skips() -> None:
    """When no provider API key is set, the phone module should return skipped."""
    module = AuthorizedPhoneLookupModule(
        settings=Settings(numverify_api_key=None, twilio_account_sid=None)
    )
    findings = await module.run("+14155552671")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.info.value
    assert f["source_status"] == SourceStatus.skipped.value
    assert "NUMVERIFY_API_KEY environment variable is not configured" in f["evidence"]


@pytest.mark.asyncio
@respx.mock
async def test_phone_provider_numverify_success() -> None:
    """When NUMVERIFY_API_KEY is configured and valid, return carrier metadata finding."""
    respx.get(
        "https://apilayer.net/api/validate?access_key=numverify-key-xyz&number=14155552671&country_code=&format=1"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": True,
                "number": "14155552671",
                "local_format": "4155552671",
                "international_format": "+14155552671",
                "country_prefix": "+1",
                "country_code": "US",
                "country_name": "United States of America",
                "location": "San Francisco",
                "carrier": "AT&T Mobility LLC",
                "line_type": "mobile",
            },
        )
    )

    module = AuthorizedPhoneLookupModule(settings=Settings(numverify_api_key="numverify-key-xyz"))
    findings = await module.run("+14155552671")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == FindingStatus.found.value
    assert f["source_status"] == SourceStatus.succeeded.value
    assert f["data"]["carrier"] == "AT&T Mobility LLC"
    assert f["data"]["line_type"] == "mobile"
