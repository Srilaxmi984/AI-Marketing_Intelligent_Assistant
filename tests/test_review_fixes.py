"""Regression tests for issues found in the pre-submission review."""

import httpx
import pytest

from app.config import settings
from app.crawler import Crawler, CrawlError, FetchedPage
from app.link_checker import LinkChecker
from app.metrics.structured_data import evaluate_structured_data
from app.metrics.title_meta import evaluate_title_meta


def _resolver(host: str):
    """Fake DNS: 'internal.example' resolves to a private address, everything else is public."""
    return ["10.0.0.5"] if host == "internal.example" else ["93.184.216.34"]


@pytest.mark.asyncio
async def test_crawler_never_requests_redirect_target_in_private_range():
    """A redirect to an internal address must be blocked BEFORE the request is sent (SSRF)."""
    requested = []

    def handler(request: httpx.Request):
        requested.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.host == "example.com":
            return httpx.Response(302, headers={"Location": "http://internal.example/admin"})
        return httpx.Response(200, text="<html><head><title>secret</title></head></html>",
                              headers={"Content-Type": "text/html"})

    crawler = Crawler(allow_private=False, dns_resolver=_resolver, transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlError) as exc_info:
        await crawler.crawl("https://example.com")

    assert exc_info.value.code == "BLOCKED_TARGET"
    assert not any("internal.example" in u for u in requested), requested


@pytest.mark.asyncio
async def test_link_checker_confirms_head_errors_with_get():
    """HEAD 403/404 followed by GET 200 is a working link, not a broken one."""
    def handler(request: httpx.Request):
        if request.url.path == "/head-hostile":
            return httpx.Response(404 if request.method == "HEAD" else 200)
        if request.url.path == "/really-missing":
            return httpx.Response(404)
        return httpx.Response(200)

    page = FetchedPage(
        url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        headers={},
        html="",
        links=["https://example.com/head-hostile", "https://example.com/really-missing"],
    )
    checker = LinkChecker(allow_private=True, transport=httpx.MockTransport(handler))
    report = await checker.check_links([page])

    by_url = {i.url: i for i in report.items}
    assert by_url["https://example.com/head-hostile"].status == "ok"
    assert by_url["https://example.com/really-missing"].status == "broken"
    assert report.broken_count == 1


def _page(html: str) -> FetchedPage:
    return FetchedPage(url="https://example.com/", final_url="https://example.com/",
                       status_code=200, headers={}, html=html)


def test_title_meta_uses_configured_thresholds(monkeypatch):
    title = "A" * 25
    desc = "B" * 80
    html = f"<html><head><title>{title}</title><meta name='description' content='{desc}'></head></html>"

    assert evaluate_title_meta([_page(html)]).passed == 0  # 25 chars < default minimum of 30
    monkeypatch.setattr(settings, "title_min_chars", 20)
    assert evaluate_title_meta([_page(html)]).passed == 1


def test_structured_data_rule_matches_what_is_measured():
    """Any parseable JSON-LD with an @type passes; the pass rule must say so honestly."""
    html = ('<html><head><script type="application/ld+json">{"@type": "SomethingCustom"}</script>'
            "</head></html>")
    result = evaluate_structured_data([_page(html)])
    assert result.passed == 1
    assert "recognized" not in result.pass_rule.lower()
    assert "@type" in result.pass_rule
