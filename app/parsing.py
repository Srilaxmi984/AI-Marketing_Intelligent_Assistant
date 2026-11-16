"""HTML parsing and metadata extraction module."""

import html
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.security import is_same_site, normalize_url

logger = logging.getLogger(__name__)


def clean_text(text: Optional[str]) -> str:
    """Decode HTML entities and collapse redundant whitespace."""
    if not text:
        return ""
    decoded = html.unescape(text)
    collapsed = " ".join(decoded.split())
    return collapsed


def extract_base_url(soup: BeautifulSoup, page_url: str) -> str:
    """Extract <base href> from <head> if present, falling back to page_url."""
    head = soup.find("head")
    if head:
        base_tag = head.find("base", href=True)
        if base_tag and base_tag.get("href"):
            return urljoin(page_url, base_tag["href"].strip())
    return page_url


def extract_title(soup: BeautifulSoup) -> Tuple[Optional[str], int]:
    """
    Extract title from <head><title>.
    An SVG <title> or <body> <title> is explicitly ignored.
    """
    head = soup.find("head")
    if not head:
        return None, 0
    # DECISION: Only <title> tags located directly in the HTML <head> are used to avoid misattributing inline SVG or body titles.
    title_tag = head.find("title")
    if not title_tag:
        return None, 0
    raw_text = title_tag.get_text()
    cleaned = clean_text(raw_text)
    if not cleaned:
        return None, 0
    return cleaned, len(cleaned)


def extract_meta_description(soup: BeautifulSoup) -> Tuple[Optional[str], int, bool]:
    """
    Extract meta description from <head>.
    Returns (cleaned_text, length, has_duplicate).
    """
    head = soup.find("head")
    if not head:
        return None, 0, False

    desc_tags = []
    for meta in head.find_all("meta"):
        name_attr = meta.get("name", "")
        if name_attr and name_attr.strip().lower() == "description":
            content = meta.get("content", "")
            desc_tags.append(content)

    if not desc_tags:
        return None, 0, False

    first_content = clean_text(desc_tags[0])
    has_duplicate = len(desc_tags) > 1
    return first_content, len(first_content), has_duplicate


def extract_canonical(
    soup: BeautifulSoup, page_url: str
) -> Tuple[Optional[str], str, Optional[str]]:
    """
    Extract canonical tag from <head>.
    Returns (resolved_canonical_url, status, error_reason).
    Possible statuses: 'self', 'points_elsewhere', 'offsite', 'missing', 'conflicting', 'invalid'.
    """
    head = soup.find("head")
    if not head:
        return None, "missing", "missing"

    base_url = extract_base_url(soup, page_url)
    canonical_tags = []
    for link in head.find_all("link"):
        rel = link.get("rel", [])
        if isinstance(rel, str):
            rel_tokens = rel.lower().split()
        else:
            rel_tokens = [r.lower() for r in rel]

        if "canonical" in rel_tokens:
            href = link.get("href", "").strip()
            if href:
                canonical_tags.append(href)

    if not canonical_tags:
        return None, "missing", "missing"

    resolved_list = []
    for href in canonical_tags:
        resolved = urljoin(base_url, href)
        parsed = urlparse(resolved)
        if parsed.scheme.lower() not in ("http", "https"):
            return href, "invalid", "invalid"
        resolved_list.append(normalize_url(resolved))

    # Check for conflicts
    unique_resolved = list(dict.fromkeys(resolved_list))
    if len(unique_resolved) > 1:
        # Multiple canonicals that resolve to different targets
        return unique_resolved[0], "conflicting", "conflicting"

    canonical_target = unique_resolved[0]

    # Check offsite
    if not is_same_site(page_url, canonical_target):
        return canonical_target, "offsite", "offsite"

    # Compare page URL and canonical ignoring fragment and trailing slash
    def strip_slash(u: str) -> str:
        parsed = urlparse(u)
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}" + (f"?{parsed.query}" if parsed.query else "")

    if strip_slash(page_url) == strip_slash(canonical_target):
        return canonical_target, "self", None

    # DECISION: Same-site canonicals pointing elsewhere pass indexability but are tagged points_elsewhere to document parameter deduplication.
    return canonical_target, "points_elsewhere", None


def parse_robots_directives(content: str) -> Set[str]:
    """Parse comma-separated directive tokens into a lowercase set."""
    tokens = set()
    for part in content.split(","):
        cleaned = part.strip().lower()
        if cleaned:
            tokens.add(cleaned)
    return tokens


def check_indexability(
    soup: BeautifulSoup, headers: Dict[str, str]
) -> Tuple[bool, List[str]]:
    """
    Check if page is indexable.
    Returns (is_indexable, reasons_failing).
    """
    failures = []
    head = soup.find("head")

    # 1. Meta tags in <head>
    if head:
        for meta in head.find_all("meta"):
            name = (meta.get("name") or "").strip().lower()
            if name in ("robots", "googlebot"):
                directives = parse_robots_directives(meta.get("content", ""))
                if "noindex" in directives or "none" in directives:
                    failures.append(f"meta_{name}_noindex")

    # 2. X-Robots-Tag response header
    for k, v in headers.items():
        if k.lower() == "x-robots-tag":
            # Header may contain multiple instructions or bot scoping
            parts = [p.strip() for p in v.split(",") if p.strip()]
            for part in parts:
                lower_part = part.lower()
                if lower_part.startswith("googlebot:"):
                    scoped_val = lower_part.split("googlebot:", 1)[1].strip()
                    if scoped_val in ("noindex", "none"):
                        failures.append("header_x_robots_tag_googlebot_noindex")
                elif ":" in lower_part:
                    # Scoped to another bot (e.g. bingbot:) -> ignore
                    continue
                else:
                    if lower_part in ("noindex", "none"):
                        failures.append("header_x_robots_tag_noindex")

    is_indexable = len(failures) == 0
    return is_indexable, failures


def extract_internal_links(soup: BeautifulSoup, page_url: str) -> Set[str]:
    """Extract valid internal links from page, resolved against base href and normalized."""
    base_url = extract_base_url(soup, page_url)
    links = set()

    for a_tag in soup.find_all("a", href=True):
        raw_href = a_tag["href"].strip()
        if not raw_href:
            continue
        lower_href = raw_href.lower()
        # Skip non-http schemes and pure fragments
        if (
            lower_href.startswith("mailto:")
            or lower_href.startswith("tel:")
            or lower_href.startswith("javascript:")
            or lower_href.startswith("data:")
            or raw_href.startswith("#")
        ):
            continue

        resolved = urljoin(base_url, raw_href)
        parsed = urlparse(resolved)
        if parsed.scheme.lower() not in ("http", "https"):
            continue

        # Keep internal only
        if is_same_site(page_url, resolved):
            normalized = normalize_url(resolved)
            links.add(normalized)

    return links


def extract_structured_data(soup: BeautifulSoup) -> Tuple[bool, List[str], List[str]]:
    """
    Extract JSON-LD structured data blocks.
    Returns (has_valid_jsonld, detected_types, errors).
    """
    detected_types = []
    errors = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        content = script.string
        if not content:
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON-LD syntax: {exc}")
            continue

        def process_node(node: Any):
            if isinstance(node, dict):
                # Handle @graph
                if "@graph" in node and isinstance(node["@graph"], list):
                    for sub in node["@graph"]:
                        process_node(sub)
                # Handle @type
                if "@type" in node:
                    t = node["@type"]
                    if isinstance(t, list):
                        for sub_t in t:
                            if isinstance(sub_t, str):
                                detected_types.append(sub_t)
                    elif isinstance(t, str):
                        detected_types.append(t)
            elif isinstance(node, list):
                for item in node:
                    process_node(item)

        process_node(data)

    has_valid = len(detected_types) > 0
    return has_valid, detected_types, errors
