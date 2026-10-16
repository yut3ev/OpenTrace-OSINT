"""Anti-SSRF (Server-Side Request Forgery) protection utilities."""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse

from opentrace.core.errors import ValidationError

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
}


def is_safe_target_host(hostname: str) -> bool:
    """Check if a hostname or IP address resolves to a safe, non-internal destination."""
    lower_host = hostname.strip().lower()
    if lower_host in BLOCKED_HOSTNAMES or lower_host.endswith(".internal"):
        return False

    try:
        ip = ipaddress.ip_address(lower_host)
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        # Not a raw IP literal; resolve host safely
        try:
            addr_info = socket.getaddrinfo(lower_host, None)
            for item in addr_info:
                sockaddr = item[4]
                ip_str = sockaddr[0]
                resolved_ip = ipaddress.ip_address(ip_str)
                if (
                    resolved_ip.is_private
                    or resolved_ip.is_loopback
                    or resolved_ip.is_link_local
                    or resolved_ip.is_multicast
                    or resolved_ip.is_reserved
                    or resolved_ip.is_unspecified
                ):
                    return False
            return True
        except socket.gaierror:
            # If host cannot be resolved, allow module request to handle standard DNS resolution error
            return True


def validate_safe_url(url: str) -> None:
    """Validate that a URL is safe to fetch and does not target internal or restricted networks."""
    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception as exc:
        raise ValidationError(f"Invalid URL structure: {exc}") from exc

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValidationError(
            f"Prohibited URL scheme '{parsed.scheme}'. Only http and https are permitted."
        )

    if not parsed.hostname:
        raise ValidationError("URL must include a valid hostname.")

    if not is_safe_target_host(parsed.hostname):
        raise ValidationError(
            f"Destination host '{parsed.hostname}' is prohibited (SSRF protection)."
        )
