"""Security and URL validation module enforcing SSRF protection."""

import ipaddress
import logging
import socket
from typing import Callable, List, Optional
from urllib.parse import urlparse, urlunparse

from app.config import settings

logger = logging.getLogger(__name__)

# Type definition for DNS resolver function
DNSResolver = Callable[[str], List[str]]


def default_dns_resolver(host: str) -> List[str]:
    """Resolve host to list of IP addresses using socket.getaddrinfo."""
    try:
        # Check if host is a numeric integer IP representation
        if host.isdigit():
            # DECISION: Numeric integer-formatted hostnames are directly parsed to prevent bypass of dotted-decimal checks.
            return [str(ipaddress.ip_address(int(host)))]
        # Check if already a valid IP string
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        pass

    try:
        results = socket.getaddrinfo(host, None)
        ips = list({item[4][0] for item in results})
        return ips
    except socket.gaierror:
        return []


def is_ip_blocked(ip_str: str) -> bool:
    """Return True if IP is private, loopback, link-local, reserved, multicast or unspecified."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def normalize_host(host: str) -> str:
    """Strip www. prefix and lowercase host for uniform comparison."""
    host_lower = host.lower()
    if host_lower.startswith("www."):
        return host_lower[4:]
    return host_lower


def is_same_site(url_a: str, url_b: str) -> bool:
    """Check if two URLs belong to the same site, treating www and bare domains as equivalent."""
    host_a = urlparse(url_a).hostname or ""
    host_b = urlparse(url_b).hostname or ""
    return normalize_host(host_a) == normalize_host(host_b)


def normalize_url(url: str) -> str:
    """
    Normalise URL:
    - lowercase scheme and host
    - drop fragment
    - drop default port (80 for http, 443 for https)
    - keep query string
    - preserve trailing slash
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()

    port = parsed.port
    # DECISION: Default HTTP/HTTPS ports are omitted to prevent duplicate crawl entries for identical resources.
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        netloc = hostname
    elif port is not None:
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    # Keep query, drop fragment
    normalized = urlunparse((scheme, netloc, parsed.path, parsed.params, parsed.query, ""))
    return normalized


def validate_url_security(
    url: str,
    allow_private: Optional[bool] = None,
    dns_resolver: Optional[DNSResolver] = None,
) -> str:
    """
    Validate URL against SSRF vulnerabilities and scheme/port restrictions.
    Returns normalized URL if valid, or raises ValueError with error code prefix.
    """
    if allow_private is None:
        allow_private = settings.allow_private_targets

    if allow_private:
        # Loud warning for dev-only mode
        print("WARNING: ALLOW_PRIVATE_TARGETS is enabled. SSRF protection for private targets is disabled.")

    resolver = dns_resolver or default_dns_resolver

    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise ValueError(f"INVALID_URL: Could not parse URL: {exc}")

    # Check scheme
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(f"INVALID_URL: Scheme '{parsed.scheme}' not allowed. Only http and https are permitted.")

    # Check userinfo
    if parsed.username or parsed.password:
        raise ValueError("INVALID_URL: User credentials in URL are prohibited.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("INVALID_URL: Hostname missing from URL.")

    # Port restriction
    port = parsed.port
    if not allow_private:
        if port is not None and port not in (80, 443):
            raise ValueError(f"INVALID_URL: Port {port} not permitted. Only 80 and 443 are allowed.")

    # SSRF Resolution and IP check
    if not allow_private:
        resolved_ips = resolver(hostname)
        if not resolved_ips:
            # DECISION: Unresolvable hosts during security validation raise BLOCKED_TARGET to halt dangerous requests early.
            raise ValueError(f"BLOCKED_TARGET: Host '{hostname}' could not be resolved.")

        for ip in resolved_ips:
            if is_ip_blocked(ip):
                raise ValueError(f"BLOCKED_TARGET: Destination address '{ip}' is in a private or restricted IP range.")

    return normalize_url(url)
