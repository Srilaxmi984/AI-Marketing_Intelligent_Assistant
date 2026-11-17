"""Internal link checker verifying link targets using HEAD and GET fallback."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional, Set

import httpx

from app.config import settings
from app.crawler import FetchedPage
from app.security import (
    DNSResolver,
    validate_url_security,
)

logger = logging.getLogger(__name__)


@dataclass
class LinkCheckItem:
    url: str
    status_code: Optional[int] = None
    status: str = "ok"  # "ok" | "broken" | "unreachable"
    error: Optional[str] = None
    found_on: List[str] = field(default_factory=list)
    is_bot_blocked: bool = False


@dataclass
class LinkCheckerReport:
    total_found: int = 0
    checked_count: int = 0
    broken_count: int = 0
    unreachable_count: int = 0
    items: List[LinkCheckItem] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timed_out: bool = False


class LinkChecker:
    """Checks discovered internal links for broken status codes."""

    def __init__(
        self,
        allow_private: Optional[bool] = None,
        dns_resolver: Optional[DNSResolver] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.allow_private = allow_private if allow_private is not None else settings.allow_private_targets
        self.dns_resolver = dns_resolver
        self.transport = transport

    async def check_single_link(
        self, client: httpx.AsyncClient, target_url: str, sources: List[str]
    ) -> LinkCheckItem:
        """Check a single target URL using HEAD with fallback to GET."""
        try:
            validate_url_security(
                target_url, allow_private=self.allow_private, dns_resolver=self.dns_resolver
            )
        except ValueError as exc:
            return LinkCheckItem(
                url=target_url,
                status_code=None,
                status="unreachable",
                error=str(exc),
                found_on=sources,
            )

        async def perform_request(method: str) -> httpx.Response:
            if method == "HEAD":
                return await client.head(target_url)
            return await client.get(target_url)

        try:
            resp = await perform_request("HEAD")
            # DECISION: HTTP 405 Method Not Allowed or 501 Not Implemented on HEAD triggers an immediate GET fallback to confirm actual link status.
            if resp.status_code in (405, 501):
                resp = await perform_request("GET")

            # Handle 429 Too Many Requests retry once
            if resp.status_code == 429:
                await asyncio.sleep(0.5)
                resp = await perform_request("GET")

            final_status = resp.status_code
            is_blocked = final_status in (403, 429)

            if final_status >= 400:
                # DECISION: Every final HTTP 4xx or 5xx response is reported as broken, including 403 and 429, to strictly match the brief definition.
                return LinkCheckItem(
                    url=target_url,
                    status_code=final_status,
                    status="broken",
                    error=f"HTTP {final_status}",
                    found_on=sources,
                    is_bot_blocked=is_blocked,
                )
            else:
                return LinkCheckItem(
                    url=target_url,
                    status_code=final_status,
                    status="ok",
                    found_on=sources,
                )

        except (httpx.TimeoutException, httpx.NetworkError, Exception) as exc:
            # DECISION: Network timeouts and connection drops are classified as unreachable and excluded from the checked denominator.
            return LinkCheckItem(
                url=target_url,
                status_code=None,
                status="unreachable",
                error=str(exc),
                found_on=sources,
            )

    async def check_links(
        self,
        pages: List[FetchedPage],
        time_budget_s: Optional[float] = None,
    ) -> LinkCheckerReport:
        """Check all unique internal links found across crawled pages, respecting an optional time budget."""
        # 1. Map target URL to source pages
        url_to_sources: Dict[str, Set[str]] = defaultdict(set)
        for page in pages:
            source = page.final_url or page.url
            for link in page.links:
                url_to_sources[link].add(source)

        total_found = len(url_to_sources)
        sorted_targets = sorted(url_to_sources.keys())[: settings.max_link_checks]

        report = LinkCheckerReport(total_found=total_found)
        if not sorted_targets:
            return report

        semaphore = asyncio.Semaphore(settings.link_check_concurrency)
        timeout = httpx.Timeout(
            connect=settings.connect_timeout_s,
            read=settings.read_timeout_s,
            write=10.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(
            transport=self.transport,
            timeout=timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
            max_redirects=settings.max_redirects,
        ) as client:

            async def sem_check(target: str) -> LinkCheckItem:
                async with semaphore:
                    sources = sorted(list(url_to_sources[target]))
                    return await self.check_single_link(client, target, sources)

            tasks = [asyncio.create_task(sem_check(target)) for target in sorted_targets]
            if time_budget_s is not None:
                done, pending = await asyncio.wait(tasks, timeout=max(0.0, time_budget_s))
                if pending:
                    report.timed_out = True
                    for p in pending:
                        p.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
            else:
                done, _ = await asyncio.wait(tasks)

            for task in done:
                if not task.cancelled():
                    try:
                        item = task.result()
                        report.items.append(item)
                        if item.status == "broken":
                            report.broken_count += 1
                            report.checked_count += 1
                            if item.is_bot_blocked:
                                report.warnings.append(
                                    f"Potential bot-blocking or rate-limiting detected (HTTP {item.status_code}) on {item.url}"
                                )
                        elif item.status == "ok":
                            report.checked_count += 1
                        elif item.status == "unreachable":
                            report.unreachable_count += 1
                    except Exception as exc:
                        logger.warning(f"Error checking link: {exc}")

        if report.timed_out:
            report.warnings.append(
                f"Link checking timed out: checked {report.checked_count} of {report.total_found} links found."
            )

        return report
