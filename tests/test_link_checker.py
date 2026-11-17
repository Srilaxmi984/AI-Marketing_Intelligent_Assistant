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


@pytest.mark.asyncio
async def test_link_checker_time_budget_timeout():
    """Verify link checking halts gracefully on timeout, records warnings, and scores only checked links."""
    import asyncio
    from app.metrics.broken_links import evaluate_broken_links

    async def async_handler(request: httpx.Request):
        url = str(request.url)
        if "slow" in url:
            await asyncio.sleep(0.3)
        return httpx.Response(200)

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links=[f"https://example.com/slow-{i}" for i in range(10)],
        )
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(async_handler))
    # Give a tiny budget of 0.05s for 10 slow requests
    report = await checker.check_links(pages, time_budget_s=0.05)

    assert report.timed_out is True
    assert report.total_found == 10
    assert report.checked_count < report.total_found
    assert any("timed out" in w for w in report.warnings)

    metric = evaluate_broken_links(report)
    assert metric.total == report.checked_count


@pytest.mark.asyncio
async def test_link_checker_redirect_to_127_blocked():
    """Verify link checker blocks intermediate redirect to 127.0.0.1 and reports it as unreachable with error 'blocked'."""
    def handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://example.com/redirect-to-127":
            return httpx.Response(301, headers={"Location": "http://127.0.0.1/admin"})
        if "127.0.0.1" in url:
            return httpx.Response(200, text="Internal Admin")
        return httpx.Response(404)

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links=["https://example.com/redirect-to-127"],
        )
    ]

    checker = LinkChecker(allow_private=False, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.unreachable_count == 1
    assert report.checked_count == 0
    assert report.broken_count == 0
    assert len(report.items) == 1
    assert report.items[0].url == "https://example.com/redirect-to-127"
    assert report.items[0].status == "unreachable"
    assert report.items[0].error == "blocked"


@pytest.mark.asyncio
async def test_link_checker_redirect_to_169_254_blocked():
    """Verify link checker blocks intermediate redirect to 169.254.169.254 and reports it as unreachable with error 'blocked'."""
    def handler(request: httpx.Request):
        url = str(request.url)
        if url == "https://example.com/redirect-to-169":
            return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data"})
        if "169.254.169.254" in url:
            return httpx.Response(200, text="Cloud Metadata")
        return httpx.Response(404)

    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links=["https://example.com/redirect-to-169"],
        )
    ]

    checker = LinkChecker(allow_private=False, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.unreachable_count == 1
    assert report.checked_count == 0
    assert report.broken_count == 0
    assert len(report.items) == 1
    assert report.items[0].url == "https://example.com/redirect-to-169"
    assert report.items[0].status == "unreachable"
    assert report.items[0].error == "blocked"


@pytest.mark.asyncio
async def test_link_checker_cap_coverage_and_warning(monkeypatch):
    """Verify that when links exceed the cap, links_found and links_unchecked are tracked, warning added, and scored on checked only."""
    from app.config import settings
    from app.metrics.broken_links import evaluate_broken_links

    monkeypatch.setattr(settings, "max_link_checks", 3)

    def handler(request: httpx.Request):
        return httpx.Response(200)

    links = [f"https://example.com/link-{i}" for i in range(5)]
    pages = [
        FetchedPage(
            url="https://example.com/page",
            final_url="https://example.com/page",
            status_code=200,
            headers={},
            html="",
            links=links,
        )
    ]

    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links(pages)

    assert report.total_found == 5
    assert report.checked_count == 3
    assert any("cap reached: 2 of 5" in w for w in report.warnings)

    metric = evaluate_broken_links(report)
    assert metric.links_found == 5
    assert metric.links_unchecked == 2
    assert "0 broken out of 3 checked; 2 of 5 internal links were not checked because of the 3-link cap." in metric.summary
    assert metric.score == 100.0
    assert metric.passed == 3
    assert metric.total == 3



