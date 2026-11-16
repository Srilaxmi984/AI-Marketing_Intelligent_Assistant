"""Tests for internal link checking, status codes, HEAD-to-GET fallback, and 429 handling."""

import pytest
import httpx

from app.crawler import FetchedPage
from app.link_checker import LinkChecker


@pytest.mark.asyncio
async def test_link_checker_detected_broken_and_source_pages():
    def handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://example.com/ok":
            return httpx.Response(200)
        if url == "https://example.com/bad-404":
            return httpx.Response(404)
        if url == "https://example.com/server-error":
            return httpx.Response(500)
        if url == "https://example.com/redirect":
            return httpx.Response(301, headers={"Location": "https://example.com/ok"})
        return httpx.Response(200)

    pages = [
        FetchedPage(
            url="https://example.com/page1",
            final_url="https://example.com/page1",
            status_code=200,
            headers={},
            html="",
            links={"https://example.com/ok", "https://example.com/bad-404", "https://example.com/redirect"},
        ),
        FetchedPage(
            url="https://example.com/page2",
            final_url="https://example.com/page2",
            status_code=200,
            headers={},
            html="",
            links={"https://example.com/bad-404", "https://example.com/server-error"},
        ),
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.checked_count == 4  # ok, bad-404, server-error, redirect
    assert report.broken_count == 2   # bad-404, server-error

    # Verify bad-404 was found on both page1 and page2
    bad_item = next(i for i in report.items if i.url == "https://example.com/bad-404")
    assert bad_item.status == "broken"
    assert "https://example.com/page1" in bad_item.found_on
    assert "https://example.com/page2" in bad_item.found_on

    # Verify redirect resolved cleanly to OK and is not broken
    redir_item = next(i for i in report.items if i.url == "https://example.com/redirect")
    assert redir_item.status == "ok"


@pytest.mark.asyncio
async def test_link_checker_head_405_fallback_to_get():
    def handler(request: httpx.Request):
        if request.method == "HEAD":
            return httpx.Response(405)
        # GET succeeds
        return httpx.Response(200, text="content")

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links={"https://example.com/no-head"},
        )
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.checked_count == 1
    assert report.broken_count == 0
    assert report.items[0].status == "ok"


@pytest.mark.asyncio
async def test_link_checker_403_and_429_reported_broken_with_warning():
    def handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://example.com/forbidden":
            return httpx.Response(403)
        if url == "https://example.com/rate-limit":
            return httpx.Response(429)
        return httpx.Response(200)

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links={"https://example.com/forbidden", "https://example.com/rate-limit"},
        )
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.broken_count == 2
    assert len(report.warnings) >= 2


@pytest.mark.asyncio
async def test_link_checker_network_timeout_reported_as_unreachable():
    def handler(request: httpx.Request):
        raise httpx.ConnectTimeout("Connection timed out")

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links={"https://example.com/timeout-link"},
        )
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.unreachable_count == 1
    assert report.checked_count == 0
    assert report.broken_count == 0
    assert report.items[0].status == "unreachable"
