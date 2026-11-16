"""Tests for HTML parsing, title, meta description, canonical, robots directives, and JSON-LD."""

from bs4 import BeautifulSoup
import pytest

from app.parsing import (
    check_indexability,
    clean_text,
    extract_canonical,
    extract_internal_links,
    extract_meta_description,
    extract_structured_data,
    extract_title,
)


class TestTitleAndMetaParsing:
    """Test title and meta description extraction rules."""

    def test_clean_text_entities_and_whitespace(self):
        raw = "  Hello &amp; Welcome &mdash;   World!  \n \t"
        assert clean_text(raw) == "Hello & Welcome — World!"

    def test_title_inside_head(self):
        html = "<html><head><title>  Proper Page Title  </title></head><body><h1>Body</h1></body></html>"
        soup = BeautifulSoup(html, "lxml")
        title, length = extract_title(soup)
        assert title == "Proper Page Title"
        assert length == len("Proper Page Title")

    def test_svg_title_ignored(self):
        html = """
        <html>
          <head></head>
          <body>
            <svg><title>SVG Diagram Title</title></svg>
            <h1>Content</h1>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        title, length = extract_title(soup)
        assert title is None
        assert length == 0

    def test_empty_or_missing_title(self):
        soup1 = BeautifulSoup("<html><head><title>   </title></head></html>", "lxml")
        assert extract_title(soup1) == (None, 0)

        soup2 = BeautifulSoup("<html><head></head></html>", "lxml")
        assert extract_title(soup2) == (None, 0)

    def test_meta_description_single_and_duplicate(self):
        html = """
        <html>
          <head>
            <meta name="Description" content="First description here.">
            <meta name="description" content="Second duplicate description.">
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        desc, length, has_dup = extract_meta_description(soup)
        assert desc == "First description here."
        assert length == len("First description here.")
        assert has_dup is True

    def test_missing_meta_description(self):
        soup = BeautifulSoup("<html><head><meta name='author' content='Jane'></head></html>", "lxml")
        desc, length, has_dup = extract_meta_description(soup)
        assert desc is None
        assert length == 0
        assert has_dup is False


class TestCanonicalParsing:
    """Test canonical link extraction, base href resolution, and conflict detection."""

    def test_canonical_self(self):
        page_url = "https://example.com/about"
        html = '<html><head><link rel="canonical" href="https://example.com/about"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert target == "https://example.com/about"
        assert status == "self"
        assert err is None

    def test_canonical_trailing_slash_counts_as_self(self):
        page_url = "https://example.com/about/"
        html = '<html><head><link rel="canonical" href="https://example.com/about"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert status == "self"

    def test_canonical_relative_with_base_href(self):
        page_url = "https://example.com/blog/post1"
        html = """
        <html>
          <head>
            <base href="https://example.com/base/">
            <link rel="canonical" href="canonical-post">
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert target == "https://example.com/base/canonical-post"
        assert status == "points_elsewhere"

    def test_canonical_points_elsewhere_same_site(self):
        page_url = "https://example.com/item?variant=2"
        html = '<html><head><link rel="canonical" href="https://example.com/item"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert target == "https://example.com/item"
        assert status == "points_elsewhere"
        assert err is None

    def test_canonical_offsite(self):
        page_url = "https://example.com/page"
        html = '<html><head><link rel="canonical" href="https://other.com/page"></head></html>'
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert target == "https://other.com/page"
        assert status == "offsite"
        assert err == "offsite"

    def test_canonical_missing(self):
        page_url = "https://example.com/page"
        soup = BeautifulSoup("<html><head></head></html>", "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert target is None
        assert status == "missing"
        assert err == "missing"

    def test_canonical_conflicting(self):
        page_url = "https://example.com/page"
        html = """
        <html>
          <head>
            <link rel="canonical" href="https://example.com/page-a">
            <link rel="canonical" href="https://example.com/page-b">
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert status == "conflicting"
        assert err == "conflicting"

    def test_canonical_identical_duplicates_not_conflicting(self):
        page_url = "https://example.com/page"
        html = """
        <html>
          <head>
            <link rel="canonical" href="https://example.com/page">
            <link rel="canonical" href="https://example.com/page">
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert status == "self"
        assert err is None

    def test_canonical_outside_head_ignored(self):
        page_url = "https://example.com/page"
        html = """
        <html>
          <head></head>
          <body>
            <link rel="canonical" href="https://example.com/page">
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        target, status, err = extract_canonical(soup, page_url)
        assert status == "missing"


class TestIndexabilityDirectives:
    """Test meta robots and X-Robots-Tag directive parsing."""

    def test_indexable_by_default(self):
        soup = BeautifulSoup("<html><head><title>OK</title></head></html>", "lxml")
        is_indexable, reasons = check_indexability(soup, {})
        assert is_indexable is True
        assert len(reasons) == 0

    def test_meta_robots_noindex_and_none(self):
        soup1 = BeautifulSoup('<html><head><meta name="robots" content="noindex, follow"></head></html>', "lxml")
        assert check_indexability(soup1, {})[0] is False

        soup2 = BeautifulSoup('<html><head><meta name="ROBOTS" content="NONE"></head></html>', "lxml")
        assert check_indexability(soup2, {})[0] is False

    def test_meta_googlebot_noindex(self):
        soup = BeautifulSoup('<html><head><meta name="googlebot" content="NoIndex"></head></html>', "lxml")
        assert check_indexability(soup, {})[0] is False

    def test_x_robots_tag_headers(self):
        soup = BeautifulSoup("<html><head></head></html>", "lxml")

        # Unscoped noindex
        assert check_indexability(soup, {"X-Robots-Tag": "noindex"})[0] is False

        # Scoped to googlebot
        assert check_indexability(soup, {"x-robots-tag": "googlebot: noindex, nofollow"})[0] is False

        # Scoped to bingbot -> ignored
        assert check_indexability(soup, {"X-Robots-Tag": "bingbot: noindex"})[0] is True


class TestStructuredDataParsing:
    """Test JSON-LD extraction, schemas, @graph, arrays."""

    def test_valid_jsonld_with_graph(self):
        html = """
        <html>
          <head>
            <script type="application/ld+json">
            {
              "@context": "https://schema.org",
              "@graph": [
                {"@type": "Organization", "name": "HubSpot"},
                {"@type": ["WebSite", "Product"], "name": "CRM"}
              ]
            }
            </script>
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        has_valid, types, errs = extract_structured_data(soup)
        assert has_valid is True
        assert "Organization" in types
        assert "WebSite" in types
        assert "Product" in types
        assert len(errs) == 0

    def test_invalid_jsonld(self):
        html = """
        <html>
          <head>
            <script type="application/ld+json">
              { not valid json }
            </script>
          </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        has_valid, types, errs = extract_structured_data(soup)
        assert has_valid is False
        assert len(types) == 0
        assert len(errs) > 0


class TestInternalLinkExtraction:
    """Test extracting internal links and skipping non-http links."""

    def test_extract_internal_links_filtering(self):
        page_url = "https://example.com/home"
        html = """
        <html>
          <body>
            <a href="/about">About</a>
            <a href="https://example.com/pricing">Pricing</a>
            <a href="https://www.example.com/contact">Contact (www)</a>
            <a href="https://external.com/blog">External</a>
            <a href="mailto:info@example.com">Email</a>
            <a href="tel:+123456789">Call</a>
            <a href="javascript:void(0)">JS</a>
            <a href="#section">Jump</a>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        links = extract_internal_links(soup, page_url)
        assert "https://example.com/about" in links
        assert "https://example.com/pricing" in links
        assert "https://www.example.com/contact" in links
        assert len(links) == 3
