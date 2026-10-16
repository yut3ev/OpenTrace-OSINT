"""Unit tests for new email modules (disposable detection, Gravatar, SPF/DMARC security)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import dns.resolver
import httpx
import pytest
import respx

from opentrace.api.schemas.common import FindingStatus
from opentrace.modules.email.disposable import DisposableEmailModule
from opentrace.modules.email.gravatar import GravatarEmailModule
from opentrace.modules.email.security import EmailSecurityModule


@pytest.mark.asyncio
async def test_disposable_email_detected() -> None:
    mod = DisposableEmailModule()
    findings = await mod.run("baduser@mailinator.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert "Disposable" in findings[0]["title"]
    assert findings[0]["data"]["is_disposable"] is True


@pytest.mark.asyncio
async def test_disposable_email_clean() -> None:
    mod = DisposableEmailModule()
    findings = await mod.run("realuser@protonmail.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value
    assert findings[0]["data"]["is_disposable"] is False


@pytest.mark.asyncio
@respx.mock
async def test_gravatar_found() -> None:
    mod = GravatarEmailModule()
    import hashlib

    email_hash = hashlib.md5(b"beau@example.com").hexdigest()

    respx.get(f"https://en.gravatar.com/{email_hash}.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "entry": [
                    {
                        "id": "12345",
                        "hash": email_hash,
                        "preferredUsername": "beau",
                        "displayName": "Beau Developer",
                        "aboutMe": "Software enthusiast",
                    }
                ]
            },
        )
    )

    findings = await mod.run("beau@example.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.found.value
    assert findings[0]["display_name"] == "Beau Developer"


@pytest.mark.asyncio
@respx.mock
async def test_gravatar_not_found() -> None:
    mod = GravatarEmailModule()
    import hashlib

    email_hash = hashlib.md5(b"nobody@example.com").hexdigest()

    respx.get(f"https://en.gravatar.com/{email_hash}.json").mock(
        return_value=httpx.Response(404, text="User not found")
    )

    findings = await mod.run("nobody@example.com")
    assert len(findings) == 1
    assert findings[0]["status"] == FindingStatus.not_found.value


@pytest.mark.asyncio
async def test_email_security_spf_and_dmarc_found() -> None:
    mod = EmailSecurityModule()

    mock_spf_rdata = MagicMock()
    mock_spf_rdata.strings = [b"v=spf1 include:_spf.google.com ~all"]

    mock_dmarc_rdata = MagicMock()
    mock_dmarc_rdata.strings = [b"v=DMARC1; p=reject; rua=mailto:d@example.com"]

    def mock_resolve(qname: str, rtype: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if qname == "example.com" and rtype == "TXT":
            return [mock_spf_rdata]
        elif qname == "_dmarc.example.com" and rtype == "TXT":
            return [mock_dmarc_rdata]
        raise dns.resolver.NXDOMAIN()

    with patch.object(dns.resolver.Resolver, "resolve", side_effect=mock_resolve):
        findings = await mod.run("user@example.com")
        assert len(findings) >= 1
        assert findings[0]["data"]["has_spf"] is True
        assert findings[0]["data"]["has_dmarc"] is True
        assert "SPF" in findings[0]["evidence"]
