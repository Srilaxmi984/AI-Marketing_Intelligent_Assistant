"""
Tests for planted defects in tests/fixture_site/.

HAND-COUNTED EXPECTATIONS FOR THE 4 PAGES IN FIXTURE SITE:
1. title_meta:
   - /: PASS (35 char title, 122 char description)
   - /page-short-title.html: FAIL (5 char title, missing description)
   - /page-noindex.html: PASS (34 char title, 101 char description)
   - /page-no-canonical.html: PASS (33 char title, 99 char description)
   => passed: 3, total: 4, score: 75.0% (warn)

2. broken_links:
   - Discovered internal links (5 unique): /, /page-short-title.html, /page-noindex.html, /page-no-canonical.html, /broken-404.html
   - Broken link: /broken-404.html (HTTP 404)
   => passed: 4, checked: 5, broken: 1, score: 80.0% (warn, broken > 0)

3. indexability_canonical:
   - /: PASS (indexable + self canonical)
   - /page-short-title.html: PASS (indexable + self canonical)
   - /page-noindex.html: FAIL (meta robots noindex)
   - /page-no-canonical.html: FAIL (missing canonical link tag)
   => passed: 2, total: 4, score: 50.0% (fail)

4. ai_crawler_access:
   - robots.txt blocks GPTBot, allows OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, Google-Extended
   => passed: 5, total: 6, score: 83.3% (warn)

5. structured_data:
   - /: PASS (Organization)
   - /page-short-title.html: PASS (WebPage)
   - /page-noindex.html: FAIL (no JSON-LD)
   - /page-no-canonical.html: PASS (Article)
   => passed: 3, total: 4, score: 75.0% (warn)

OVERALL EXPECTED SCORE:
   = 0.25 * 50.0 + 0.20 * 75.0 + 0.20 * 83.3 + 0.20 * 75.0 + 0.15 * 80.0
   = 12.50 + 15.00 + 16.66 + 15.00 + 12.00 = 71.16 => 71.2
"""

from pathlib import Path
import pytest
import httpx

from app.crawler import Crawler
from app.link_checker import LinkChecker
from app.metrics.ai_crawler_access import evaluate_ai_crawler_access
from app.metrics.broken_links import evaluate_broken_links
from app.metrics.indexability_canonical import evaluate_indexability_canonical
from app.metrics.structured_data import evaluate_structured_data
from app.metrics.title_meta import evaluate_title_meta
from app.scoring import calculate_overall_score

FIXTURE_DIR = Path(__file__).parent / "fixture_site"


def make_fixture_transport():
    """Mock transport reading directly from fixture_site files."""
    def handler(request: httpx.Request):
        path = request.url.path
        if path == "/" or path == "":
            path = "/index.html"

        file_path = FIXTURE_DIR / path.lstrip("/")
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            content_type = "text/plain" if path.endswith((".txt",)) else "text/html"
            return httpx.Response(200, text=content, headers={"Content-Type": content_type})

        # Return 404 for missing paths like /broken-404.html
        return httpx.Response(404, text="Not Found", headers={"Content-Type": "text/html"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_fixture_site_hand_counted_audit():
    transport = make_fixture_transport()
    start_url = "http://127.0.0.1:8000/"

    crawler = Crawler(max_pages=25, allow_private=True, transport=transport)
    crawl_result = await crawler.crawl(start_url)

    assert len(crawl_result.pages) == 4
    assert crawl_result.has_llms_txt is True

    # Check links
    checker = LinkChecker(allow_private=True, transport=transport)
    link_report = await checker.check_links(crawl_result.pages)

    # 1. title_meta: 3/4 passed = 75.0%
    m_title = evaluate_title_meta(crawl_result.pages)
    assert m_title.passed == 3
    assert m_title.total == 4
    assert m_title.score == 75.0
    assert m_title.status == "warn"

    # 2. broken_links: 4/5 passed, 1 broken = 80.0%
    m_links = evaluate_broken_links(link_report)
    assert m_links.passed == 4
    assert m_links.total == 5
    assert m_links.score == 80.0
    assert m_links.status == "warn"
    assert len(m_links.details) == 1
    assert "broken-404.html" in m_links.details[0]["url"]

    # 3. indexability_canonical: 2/4 passed = 50.0%
    m_index = evaluate_indexability_canonical(crawl_result.pages)
    assert m_index.passed == 2
    assert m_index.total == 4
    assert m_index.score == 50.0
    assert m_index.status == "fail"

    # 4. ai_crawler_access: 5/6 passed = 83.3%
    m_ai = evaluate_ai_crawler_access(crawl_result.robots_parser, start_url, crawl_result.has_llms_txt)
    assert m_ai.passed == 5
    assert m_ai.total == 6
    assert m_ai.score == 83.3
    assert m_ai.status == "warn"

    # 5. structured_data: 3/4 passed = 75.0%
    m_schema = evaluate_structured_data(crawl_result.pages)
    assert m_schema.passed == 3
    assert m_schema.total == 4
    assert m_schema.score == 75.0
    assert m_schema.status == "warn"

    # Overall score = 71.2
    overall = calculate_overall_score([m_title, m_links, m_index, m_ai, m_schema])
    assert overall.score == 71.2
