"""Unit tests for email modules including syntax validation and mocked DNS MX lookups."""

from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
import pytest

from opentrace.modules.email.dns import EmailDNSModule
from opentrace.modules.email.syntax import EmailSyntaxModule


@pytest.mark.asyncio
async def test_email_syntax_valid():
    mod = EmailSyntaxModule()
    findings = await mod.run("test.user@example.com")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "info"
    assert f["confidence"] == "high"
    assert f["data"]["domain"] == "example.com"
    assert f["data"]["local_part"] == "test.user"


@pytest.mark.asyncio
async def test_email_syntax_invalid():
    mod = EmailSyntaxModule()
    findings = await mod.run("invalid-email-no-at-sign")
    assert len(findings) == 1
    assert findings[0]["status"] == "error"
    assert findings[0]["confidence"] == "none"


@pytest.mark.asyncio
async def test_email_dns_mx_found():
    mod = EmailDNSModule()

    # Mock DNS MX rdata
    mock_mx = MagicMock()
    mock_mx.preference = 10
    mock_mx.exchange = "mail.example.com."

    with patch.object(dns.resolver.Resolver, "resolve", return_value=[mock_mx]):
        findings = await mod.run("user@example.com")

    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "info"
    assert f["confidence"] == "medium"
    assert f["data"]["has_mx"] is True
    assert f["data"]["mx_records"][0]["exchange"] == "mail.example.com"
    assert f["data"]["mx_records"][0]["preference"] == 10


@pytest.mark.asyncio
async def test_email_dns_no_mx():
    mod = EmailDNSModule()

    with patch.object(dns.resolver.Resolver, "resolve", side_effect=dns.resolver.NoAnswer):
        findings = await mod.run("user@example.com")

    assert len(findings) == 1
    assert findings[0]["status"] == "not_found"


@pytest.mark.asyncio
async def test_email_dns_timeout():
    mod = EmailDNSModule()

    with patch.object(dns.resolver.Resolver, "resolve", side_effect=dns.exception.Timeout):
        findings = await mod.run("user@example.com")

    assert len(findings) == 1
    assert findings[0]["status"] == "unknown"
