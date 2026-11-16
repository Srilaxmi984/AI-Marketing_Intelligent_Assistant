"""Tests for URL validation, SSRF checks, and URL normalisation."""

import pytest
from app.security import (
    is_same_site,
    normalize_host,
    normalize_url,
    validate_url_security,
)


def mock_dns_resolver_private(host: str):
    """Resolver mock returning loopback/private addresses."""
    if host in ("localhost", "127.0.0.1"):
        return ["127.0.0.1"]
    if host == "169.254.169.254":
        return ["169.254.169.254"]
    if host == "10.0.0.1":
        return ["10.0.0.1"]
    if host in ("::1", "[::1]"):
        return ["::1"]
    return ["192.168.1.1"]


def mock_dns_resolver_public(host: str):
    """Resolver mock returning public IP addresses."""
    return ["93.184.216.34"]


class TestSecurityValidation:
    """SSRF and URL format security tests."""

    @pytest.mark.parametrize(
        "blocked_url",
        [
            "http://127.0.0.1/test",
            "http://localhost/test",
            "http://169.254.169.254/latest/meta-data",
            "http://10.0.0.1/admin",
            "http://[::1]/status",
            "http://2130706433/path",  # Decimal encoded 127.0.0.1
            "file:///etc/passwd",
            "ftp://example.com/file",
            "http://user:password@example.com/",
            "https://example.com:8080/dashboard",  # Disallowed port
        ],
    )
    def test_security_blocks_restricted_urls(self, blocked_url):
        with pytest.raises(ValueError) as exc_info:
            validate_url_security(
                blocked_url,
                allow_private=False,
                dns_resolver=mock_dns_resolver_private,
            )
        err = str(exc_info.value)
        assert "INVALID_URL" in err or "BLOCKED_TARGET" in err

    def test_security_allows_valid_public_url(self):
        url = "https://EXAMPLE.COM/about?ref=1#heading"
        validated = validate_url_security(
            url,
            allow_private=False,
            dns_resolver=mock_dns_resolver_public,
        )
        assert validated == "https://example.com/about?ref=1"

    def test_security_allow_private_flag(self):
        # When allow_private is explicitly True, local addresses and custom ports are permitted
        local_url = "http://127.0.0.1:8000/fixture"
        validated = validate_url_security(
            local_url,
            allow_private=True,
            dns_resolver=mock_dns_resolver_private,
        )
        assert validated == "http://127.0.0.1:8000/fixture"


class TestUrlNormalization:
    """URL normalization and site-matching tests."""

    def test_normalize_lowercase_and_fragment(self):
        raw = "HTTPS://Sub.Example.COM/Path/To/Page?query=yes#section"
        norm = normalize_url(raw)
        assert norm == "https://sub.example.com/Path/To/Page?query=yes"

    def test_normalize_drops_default_ports(self):
        assert normalize_url("http://example.com:80/hello") == "http://example.com/hello"
        assert normalize_url("https://example.com:443/hello") == "https://example.com/hello"
        assert normalize_url("http://example.com:8080/hello") == "http://example.com:8080/hello"

    def test_normalize_preserves_trailing_slash(self):
        assert normalize_url("https://example.com/dir/") == "https://example.com/dir/"
        assert normalize_url("https://example.com/dir") == "https://example.com/dir"

    def test_is_same_site(self):
        assert is_same_site("https://www.hubspot.com/blog", "https://hubspot.com/pricing")
        assert is_same_site("http://example.com", "https://www.example.com/path")
        assert not is_same_site("https://hubspot.com", "https://google.com")
        assert not is_same_site("https://blog.hubspot.com", "https://hubspot.com")
