"""Unit tests for phone numbering plan metadata module."""

import pytest

from opentrace.modules.phone.numbering import PhoneNumberingModule


@pytest.mark.asyncio
async def test_phone_numbering_valid_us():
    mod = PhoneNumberingModule()
    findings = await mod.run("+12025550123")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "info"
    assert f["confidence"] == "high"
    assert f["data"]["e164"] == "+12025550123"
    assert f["data"]["country_calling_code"] == 1
    assert f["data"]["region_code"] == "US"


@pytest.mark.asyncio
async def test_phone_numbering_valid_uk():
    mod = PhoneNumberingModule()
    findings = await mod.run("+442079460999")
    assert len(findings) == 1
    f = findings[0]
    assert f["status"] == "info"
    assert f["data"]["region_code"] == "GB"


@pytest.mark.asyncio
async def test_phone_numbering_invalid_parse():
    mod = PhoneNumberingModule()
    findings = await mod.run("abc-not-a-number")
    assert len(findings) == 1
    assert findings[0]["status"] == "error"
    assert findings[0]["confidence"] == "none"


@pytest.mark.asyncio
async def test_phone_numbering_impossible_length():
    mod = PhoneNumberingModule()
    findings = await mod.run("+123")
    assert len(findings) == 1
    assert findings[0]["status"] == "error"
