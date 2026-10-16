"""Unit tests for target normalization functions."""

import pytest

from opentrace.core.errors import ValidationError
from opentrace.core.normalization import (
    normalize_email,
    normalize_phone,
    normalize_username,
)


def test_normalize_username_valid():
    assert normalize_username("octocat") == "octocat"
    assert normalize_username("  OctoCat  ") == "octocat"
    assert normalize_username("user-name_123") == "user-name_123"
    assert normalize_username("john.doe") == "john.doe"


def test_normalize_username_invalid():
    with pytest.raises(ValidationError):
        normalize_username("")

    with pytest.raises(ValidationError):
        normalize_username("   ")

    with pytest.raises(ValidationError):
        # Exceeds 39 characters
        normalize_username("a" * 40)

    with pytest.raises(ValidationError):
        # Invalid characters (e.g. spaces in between, symbols)
        normalize_username("invalid user!")


def test_normalize_email_valid():
    assert normalize_email("user@example.com") == "user@example.com"
    assert normalize_email("  User@Example.COM  ") == "user@example.com"
    assert normalize_email("first.last+tag@sub.domain.org") == "first.last+tag@sub.domain.org"


def test_normalize_email_idna():
    # Domain with non-ascii characters should normalize to IDNA punycode
    normalized = normalize_email("test@münchen.de")
    assert normalized.startswith("test@xn--mnchen-3ya.de")


def test_normalize_email_invalid():
    with pytest.raises(ValidationError):
        normalize_email("")

    with pytest.raises(ValidationError):
        normalize_email("notanemail")

    with pytest.raises(ValidationError):
        normalize_email("@nodomain.com")

    with pytest.raises(ValidationError):
        normalize_email("missingdomain@")


def test_normalize_phone_valid():
    # US number
    assert normalize_phone("+1 202-555-0123") == "+12025550123"
    # UK number
    assert normalize_phone("+44 20 7946 0999") == "+442079460999"


def test_normalize_phone_invalid():
    with pytest.raises(ValidationError):
        normalize_phone("")

    with pytest.raises(ValidationError):
        normalize_phone("not a number")

    with pytest.raises(ValidationError):
        # Impossible length
        normalize_phone("+1 23")
