"""Asynchronous breadth-first web crawler with robots.txt enforcement and SSRF protection."""

import asyncio
from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import httpx
from protego import Protego

from app.config import settings
from app.parsing import extract_internal_links
from app.security import (
    DNSResolver,
    is_same_site,
    normalize_url,
    validate_url_security,
)

logger = logging.getLogger(__name__)


class CrawlError(Exception):
    """Exception raised during crawling with an error code and message."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FetchedPage:
    url: str
    final_url: str
    status_code: int
    headers: Dict[str, str]
    html: str
    links: List[str] = field(default_factory=list)


@dataclass
class CrawlResult:
    pages: List[FetchedPage] = field(default_factory=list)
    pages_discovered: int = 0
    truncated: bool = False
    truncated_reason: Optional[str] = None
    duration_s: float = 0.0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    skipped_by_robots: List[str] = field(default_factory=list)
    robots_parser: Optional[Protego] = None
    robots_status_code: int = 404
    has_llms_txt: bool = False


async def fetch_robots_txt(
    client: httpx.AsyncClient,
    start_url: str,
    allow_private: bool,
    dns_resolver: Optional[DNSResolver] = None,
) -> Tuple[Protego, int]:
    """Fetch and parse /robots.txt following RFC 9309 rules."""
    robots_url = urljoin(start_url, "/robots.txt")
    try:
        validate_url_security(robots_url, allow_private=allow_private, dns_resolver=dns_resolver)
        resp = await client.get(robots_url, headers={"User-Agent": settings.user_agent})
        # DECISION: RFC 9309 specifies that 4xx HTTP responses allow full crawler access, while 5xx servers disallow all crawling.
        if resp.status_code == 200:
            return Protego.parse(resp.text), 200
        elif 400 <= resp.status_code < 500:
            return Protego.parse(""), resp.status_code
        else:
            return Protego.parse("User-agent: *\nDisallow: /"), resp.status_code
    except Exception:
        # Network or resolution errors default to disallowing all per RFC 9309
        return Protego.parse("User-agent: *\nDisallow: /"), 500


async def check_llms_txt(
    client: httpx.AsyncClient,
    start_url: str,
    allow_private: bool,
    dns_resolver: Optional[DNSResolver] = None,
) -> bool:
    """Check if /llms.txt exists and is accessible."""
    llms_url = urljoin(start_url, "/llms.txt")
    try:
        validate_url_security(llms_url, allow_private=allow_private, dns_resolver=dns_resolver)
        resp = await client.get(llms_url, headers={"User-Agent": settings.user_agent})
        return resp.status_code == 200
    except Exception:
        return False


class Crawler:
    """Breadth-first crawler with rate limiting, timeouts, and boundary checks."""

    def __init__(
        self,
        max_pages: Optional[int] = None,
        allow_private: Optional[bool] = None,
        dns_resolver: Optional[DNSResolver] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
        time_budget_s: Optional[float] = None,
    ):
        self.max_pages = min(max_pages or settings.default_max_pages, settings.max_pages_cap)
        self.allow_private = allow_private if allow_private is not None else settings.allow_private_targets
        self.dns_resolver = dns_resolver
        self.transport = transport
        self.time_budget_s = time_budget_s if time_budget_s is not None else settings.crawl_budget_s

    async def crawl(self, start_url: str) -> CrawlResult:
        start_time = time.monotonic()
        normalized_start = validate_url_security(
            start_url, allow_private=self.allow_private, dns_resolver=self.dns_resolver
        )

        timeout = httpx.Timeout(
            connect=settings.connect_timeout_s,
            read=settings.read_timeout_s,
            write=10.0,
            pool=10.0,
        )

        result = CrawlResult()

        async with httpx.AsyncClient(
            transport=self.transport,
            timeout=timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
            max_redirects=settings.max_redirects,
        ) as client:
            # 1. Fetch robots.txt and llms.txt
            robots_parser, robots_status = await fetch_robots_txt(
                client, normalized_start, self.allow_private, self.dns_resolver
            )
            result.robots_parser = robots_parser
            result.robots_status_code = robots_status
            result.has_llms_txt = await check_llms_txt(
                client, normalized_start, self.allow_private, self.dns_resolver
            )

            # Check if start URL is allowed by robots.txt
            if not robots_parser.can_fetch(normalized_start, settings.user_agent):
                raise CrawlError("ROBOTS_DISALLOWED", f"Crawling start URL disallowed by robots.txt: {normalized_start}")

            queue: List[Tuple[str, int]] = [(normalized_start, 0)]
            discovered: Set[str] = {normalized_start}
            fetched_urls: Set[str] = set()

            # BFS crawl loop
            semaphore = asyncio.Semaphore(settings.crawl_concurrency)

            while queue and len(result.pages) < self.max_pages:
                # Check crawl budget
                if time.monotonic() - start_time >= self.time_budget_s:
                    result.truncated = True
                    result.truncated_reason = f"Crawl time budget exceeded ({self.time_budget_s}s)"
                    break

                # Pop current item
                current_url, depth = queue.pop(0)
                if current_url in fetched_urls:
                    continue

                # Check robots.txt
                if not robots_parser.can_fetch(current_url, settings.user_agent):
                    result.skipped_by_robots.append(current_url)
                    continue

                fetched_urls.add(current_url)

                async with semaphore:
                    try:
                        validate_url_security(
                            current_url, allow_private=self.allow_private, dns_resolver=self.dns_resolver
                        )
                        # Fetch page
                        resp = await client.get(current_url)

                        # Validate redirect hops for SSRF and offsite redirects
                        final_url = str(resp.url)
                        for hop in resp.history:
                            validate_url_security(
                                str(hop.url), allow_private=self.allow_private, dns_resolver=self.dns_resolver
                            )
                        validate_url_security(
                            final_url, allow_private=self.allow_private, dns_resolver=self.dns_resolver
                        )

                        # If start page redirected offsite, abort
                        if current_url == normalized_start and not is_same_site(normalized_start, final_url):
                            raise CrawlError(
                                "REDIRECTED_OFFSITE",
                                f"Start URL redirected to foreign site: {final_url}",
                            )

                        if resp.status_code >= 400:
                            # DECISION: Non-2xx crawl responses are categorized as fetch errors and excluded from page metrics.
                            result.errors.append({
                                "url": current_url,
                                "status_code": resp.status_code,
                                "error": f"HTTP {resp.status_code}",
                            })
                            if current_url == normalized_start:
                                raise CrawlError("UNREACHABLE_SITE", f"Start URL returned HTTP {resp.status_code}")
                            continue

                        content_type = resp.headers.get("content-type", "").lower()
                        if current_url == normalized_start and "text/html" not in content_type:
                            raise CrawlError("NOT_HTML", f"Start URL returned non-HTML content-type: {content_type}")

                        if "text/html" not in content_type:
                            continue

                        # Check body size cap
                        body_bytes = resp.content
                        if len(body_bytes) > settings.max_body_bytes:
                            # DECISION: Pages exceeding the 2 MB body cap are truncated to safeguard memory and audit performance.
                            html_text = body_bytes[: settings.max_body_bytes].decode("utf-8", errors="replace")
                        else:
                            html_text = resp.text

                        soup = BeautifulSoup(html_text, "lxml")
                        links = extract_internal_links(soup, final_url)

                        # Store fetched page
                        header_dict = {k.lower(): v for k, v in resp.headers.items()}
                        page = FetchedPage(
                            url=current_url,
                            final_url=normalize_url(final_url),
                            status_code=resp.status_code,
                            headers=header_dict,
                            html=html_text,
                            links=links,
                        )
                        result.pages.append(page)

                        # DECISION: Queue discovered links in first-seen document order without sorting to honor source page structure.
                        if depth + 1 <= settings.max_crawl_depth:
                            for link in links:
                                if link not in discovered:
                                    discovered.add(link)
                                    queue.append((link, depth + 1))

                    except CrawlError:
                        raise
                    except Exception as exc:
                        logger.warning(f"Error fetching {current_url}: {exc}")
                        result.errors.append({"url": current_url, "error": str(exc)})
                        if current_url == normalized_start:
                            raise CrawlError("UNREACHABLE_SITE", f"Failed to fetch start URL: {exc}")

            result.pages_discovered = len(discovered)
            result.duration_s = round(time.monotonic() - start_time, 2)

            if not result.pages and not result.errors:
                raise CrawlError("UNREACHABLE_SITE", "No pages could be fetched from the target site.")

            return result
