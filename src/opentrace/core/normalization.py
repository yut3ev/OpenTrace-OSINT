"""Input normalization for all target types."""

from __future__ import annotations

import re

import phonenumbers

from opentrace.core.errors import ValidationError

# Username: alphanumeric, hyphens, underscores, dots. Max 39 chars (GitHub limit).
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$")
_MAX_USERNAME_LEN = 39

# Email: simplified RFC 5321 local-part + domain validation
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def normalize_username(raw: str) -> str:
    """Normalize and validate a username.

    Returns lowercase, stripped username. Raises ValidationError on invalid input.
    """
    username = raw.strip().lower()
    if not username:
        raise ValidationError("Username cannot be empty")
    if len(username) > _MAX_USERNAME_LEN:
        raise ValidationError(f"Username exceeds {_MAX_USERNAME_LEN} characters")
    if not _USERNAME_RE.match(username):
        raise ValidationError(
            "Username must contain only alphanumeric characters, hyphens, underscores, or dots"
        )
    return username


def normalize_email(raw: str) -> str:
    """Normalize and validate an email address.

    Returns lowercase email with IDNA-encoded domain. Raises ValidationError on invalid input.
    """
    email = raw.strip().lower()
    if not email:
        raise ValidationError("Email cannot be empty")
    if "@" not in email:
        raise ValidationError("Invalid email format")

    parts = email.rsplit("@", 1)
    if len(parts) != 2:
        raise ValidationError("Invalid email format")

    local, domain = parts
    if not local or not domain:
        raise ValidationError("Invalid email format")

    try:
        # IDNA encode the domain (handles internationalized domain names)
        domain = domain.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"Invalid email domain: {domain}") from exc

    normalized = f"{local}@{domain}"
    if not _EMAIL_RE.match(normalized):
        raise ValidationError("Invalid email format")

    return normalized


def normalize_phone(raw: str) -> str:
    """Normalize and validate a phone number to E.164 format.

    Raises ValidationError on invalid input.
    """
    raw = raw.strip()
    if not raw:
        raise ValidationError("Phone number cannot be empty")
    try:
        parsed = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException as exc:
        raise ValidationError(f"Invalid phone number: {exc}") from exc

    if not phonenumbers.is_possible_number(parsed):
        raise ValidationError("Phone number is not a possible number")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
