"""Tests for breadth-first crawler and robots.txt handling using MockTransport."""

import pytest
import httpx
from protego import Protego

from app.crawler import Crawler, CrawlError


def make_mock_handler():
    """Mock HTTP handler simulating a multi-page site with robots.txt."""
    def handler(request: httpx.Request):
        url = str(request.url)

        if url.endswith("/robots.txt"):
            content = """User-agent: *
Disallow: /private/
Disallow: /admin/*
Allow: /admin/public
"""
            return httpx.Response(200, text=content, headers={"Content-Type": "text/plain"})

        if url.endswith("/llms.txt"):
            return httpx.Response(200, text="# LLMs documentation", headers={"Content-Type": "text/plain"})

        if url == "https://example.com" or url == "https://example.com/":
            html = """
            <html>
              <head><title>Home Page</title></head>
              <body>
                <a href="/about">About</a>
                <a href="/private/secret">Secret</a>
                <a href="/admin/dashboard">Admin Dash</a>
                <a href="/admin/public">Admin Public</a>
                <a href="https://other.com/out">External</a>
              </body>
            </html>
            """
            return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})

        if url == "https://example.com/about":
            html = "<html><head><title>About</title></head><body><a href='/contact'>Contact</a></body></html>"
            return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})

        if url == "https://example.com/contact":
            html = "<html><head><title>Contact</title></head><body><p>Contact Us</p></body></html>"
            return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})

        if url == "https://example.com/admin/public":
            html = "<html><head><title>Admin Public</title></head><body><p>Public Admin</p></body></html>"
            return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})

        return httpx.Response(404, text="Not Found", headers={"Content-Type": "text/html"})

    return handler


@pytest.mark.asyncio
async def test_crawler_bfs_and_robots_rules():
    transport = httpx.MockTransport(make_mock_handler())
    crawler = Crawler(
        max_pages=10,
        allow_private=True,
        transport=transport,
    )

    result = await crawler.crawl("https://example.com")
    crawled_urls = [p.url for p in result.pages]

    # Verify allowed pages were crawled
    assert "https://example.com" in crawled_urls
    assert "https://example.com/about" in crawled_urls
    assert "https://example.com/contact" in crawled_urls
    assert "https://example.com/admin/public" in crawled_urls

    # Verify disallowed pages were skipped and listed
    assert "https://example.com/private/secret" in result.skipped_by_robots
    assert "https://example.com/admin/dashboard" in result.skipped_by_robots
    assert "https://example.com/private/secret" not in crawled_urls

    # Verify llms.txt detected
    assert result.has_llms_txt is True


@pytest.mark.asyncio
async def test_crawler_start_page_robots_disallowed():
    def handler(request: httpx.Request):
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(200, text="User-agent: *\nDisallow: /", headers={"Content-Type": "text/plain"})
        return httpx.Response(200, text="<html><body>Home</body></html>", headers={"Content-Type": "text/html"})

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlError) as exc_info:
        await crawler.crawl("https://example.com")
    assert exc_info.value.code == "ROBOTS_DISALLOWED"


@pytest.mark.asyncio
async def test_crawler_robots_404_allows_all():
    def handler(request: httpx.Request):
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(404, text="Not Found")
        return httpx.Response(200, text="<html><head><title>T</title></head><body>Page</body></html>", headers={"Content-Type": "text/html"})

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    result = await crawler.crawl("https://example.com")
    assert len(result.pages) == 1
    assert result.robots_status_code == 404


@pytest.mark.asyncio
async def test_crawler_robots_500_disallows_all():
    def handler(request: httpx.Request):
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(500, text="Server Error")
        return httpx.Response(200, text="<html><body>Page</body></html>", headers={"Content-Type": "text/html"})

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlError) as exc_info:
        await crawler.crawl("https://example.com")
    assert exc_info.value.code == "ROBOTS_DISALLOWED"


@pytest.mark.asyncio
async def test_crawler_redirected_offsite():
    def handler(request: httpx.Request):
        url = str(request.url)
        if url.endswith("/robots.txt"):
            return httpx.Response(404)
        if "different-domain.com" in url:
            return httpx.Response(200, text="<html><body>Foreign</body></html>", headers={"Content-Type": "text/html"})
        return httpx.Response(
            302,
            headers={"Location": "https://different-domain.com/"},
        )

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlError) as exc_info:
        await crawler.crawl("https://example.com")
    assert exc_info.value.code == "REDIRECTED_OFFSITE"


@pytest.mark.asyncio
async def test_crawler_not_html():
    def handler(request: httpx.Request):
        if str(request.url).endswith("/robots.txt"):
            return httpx.Response(404)
        return httpx.Response(200, content=b"%PDF-1.4", headers={"Content-Type": "application/pdf"})

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    with pytest.raises(CrawlError) as exc_info:
        await crawler.crawl("https://example.com")
    assert exc_info.value.code == "NOT_HTML"


@pytest.mark.asyncio
async def test_crawler_html_content_type_accepted_and_preserved():
    """Regression test: verify HTML with Content-Type: text/html is accepted and preserved."""
    def handler(request: httpx.Request):
        url = str(request.url)
        if url.endswith("/robots.txt"):
            return httpx.Response(404)
        if url.endswith("/llms.txt"):
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="<!DOCTYPE html><html><head><title>Test</title></head><body>Hello</body></html>",
            headers={"Content-Type": "text/html; charset=UTF-8", "X-Custom-Header": "PreservedValue"},
        )

    crawler = Crawler(allow_private=True, transport=httpx.MockTransport(handler))
    result = await crawler.crawl("https://example.com")

    assert len(result.pages) == 1
    page = result.pages[0]
    assert page.url == "https://example.com"
    assert page.status_code == 200
    assert "content-type" in page.headers
    assert "text/html" in page.headers["content-type"]
    assert page.headers["content-type"] == "text/html; charset=UTF-8"
    assert page.headers.get("x-custom-header") == "PreservedValue"
