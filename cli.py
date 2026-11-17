"""Command-line interface for running SEO audits and writing report files."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from urllib.parse import urlparse
import uuid

from app.config import settings
from app.crawler import Crawler, CrawlError
from app.link_checker import LinkChecker
from app.llm import generate_action_list
from app.metrics.ai_crawler_access import evaluate_ai_crawler_access
from app.metrics.broken_links import evaluate_broken_links
from app.metrics.indexability_canonical import evaluate_indexability_canonical
from app.metrics.structured_data import evaluate_structured_data
from app.metrics.title_meta import evaluate_title_meta
from app.schemas import AuditResponse, CrawlStats
from app.scoring import calculate_overall_score
from app.security import validate_url_security

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("cli")


async def execute_audit(url: str, max_pages: int) -> AuditResponse:
    """Run complete audit pipeline for given target URL."""
    request_start = time.monotonic()
    deadline = request_start + settings.total_budget_s
    started_at = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())

    normalized_url = validate_url_security(url)
    logger.info(f"Starting audit for {normalized_url} (max pages: {max_pages})...")

    # Stage 1: Crawl
    t_crawl_start = time.monotonic()
    crawl_budget = min(settings.crawl_budget_s, max(0.0, deadline - time.monotonic()))
    crawler = Crawler(max_pages=max_pages, time_budget_s=crawl_budget)
    crawl_result = await crawler.crawl(normalized_url)
    crawl_dur = round(time.monotonic() - t_crawl_start, 2)

    logger.info(f"Crawled {len(crawl_result.pages)} pages in {crawl_result.duration_s}s (bounded by CRAWL_BUDGET_S={settings.crawl_budget_s}s).")
    logger.info("Checking internal links (bounded by remaining TOTAL_BUDGET_S)...")

    # Stage 2: Link checks
    t_links_start = time.monotonic()
    remaining_for_links = max(0.0, deadline - time.monotonic())
    link_checker = LinkChecker()
    link_report = await link_checker.check_links(crawl_result.pages, time_budget_s=remaining_for_links)
    links_dur = round(time.monotonic() - t_links_start, 2)

    logger.info("Evaluating 5 SEO metrics...")
    metric_title_meta = evaluate_title_meta(crawl_result.pages)
    metric_broken_links = evaluate_broken_links(link_report)
    metric_indexability = evaluate_indexability_canonical(crawl_result.pages)
    metric_ai_crawler = evaluate_ai_crawler_access(
        crawl_result.robots_parser, normalized_url, crawl_result.has_llms_txt
    )
    metric_structured_data = evaluate_structured_data(crawl_result.pages)

    metrics_list = [
        metric_title_meta,
        metric_broken_links,
        metric_indexability,
        metric_ai_crawler,
        metric_structured_data,
    ]

    overall = calculate_overall_score(metrics_list)

    # Stage 3: LLM call
    logger.info(f"Generating marketing actions (bounded by LLM_TOTAL_BUDGET_S={settings.llm_total_budget_s}s)...")
    t_llm_start = time.monotonic()
    actions = await generate_action_list(metrics_list)
    llm_dur = round(time.monotonic() - t_llm_start, 2)

    total_dur = round(time.monotonic() - request_start, 2)

    warnings = list(link_report.warnings)
    if crawl_result.truncated:
        warnings.append(f"Crawl truncated: {crawl_result.truncated_reason}")

    finished_at = datetime.now(timezone.utc).isoformat()

    crawl_stats = CrawlStats(
        pages_crawled=len(crawl_result.pages),
        pages_discovered=crawl_result.pages_discovered,
        max_pages=max_pages,
        truncated=crawl_result.truncated,
        truncated_reason=crawl_result.truncated_reason,
        duration_s=crawl_result.duration_s,
        errors=crawl_result.errors,
        skipped_by_robots=crawl_result.skipped_by_robots,
    )

    return AuditResponse(
        audit_id=audit_id,
        url=normalized_url,
        started_at=started_at,
        finished_at=finished_at,
        total_duration_s=total_dur,
        stage_durations={
            "crawl": crawl_dur,
            "link_checks": links_dur,
            "llm": llm_dur,
        },
        links_found=metric_broken_links.links_found,
        links_unchecked=metric_broken_links.links_unchecked,
        crawl=crawl_stats,
        metrics=metrics_list,
        overall=overall,
        actions=actions,
        warnings=warnings,
    )


def print_summary(response: AuditResponse):
    """Print readable terminal report."""
    print("\n" + "=" * 70)
    print("  AI MARKETING INTELLIGENCE ASSISTANT - SEO AUDIT REPORT")
    print("=" * 70)
    print(f"Target URL:        {response.url}")
    print(f"Audit ID:          {response.audit_id}")
    print(f"Pages Crawled:     {response.crawl.pages_crawled} (discovered: {response.crawl.pages_discovered})")
    print(f"Total Duration:    {response.total_duration_s}s (crawl: {response.stage_durations.get('crawl', 0)}s [bounded by CRAWL_BUDGET_S={settings.crawl_budget_s}s], links: {response.stage_durations.get('link_checks', 0)}s [bounded by TOTAL_BUDGET_S={settings.total_budget_s}s], llm: {response.stage_durations.get('llm', 0)}s [bounded by LLM_TOTAL_BUDGET_S={settings.llm_total_budget_s}s], worst-case total: {settings.total_budget_s + settings.llm_total_budget_s}s)")
    print("-" * 70)
    print(f"OVERALL HEALTH SCORE: {response.overall.score} / 100")
    print(f"Scoring Formula:     {response.overall.formula}")
    print("-" * 70)
    print("THE FIVE CORE METRICS:")
    for idx, m in enumerate(response.metrics, 1):
        status_tag = f"[{m.status.upper()}]"
        print(f" {idx}. {m.name.ljust(35)} {status_tag.ljust(8)} Score: {str(m.score).rjust(5)}% ({m.passed}/{m.total})")
        print(f"    Summary: {m.summary}")

    print("-" * 70)
    fallback_note = f" (fallback: {response.actions.fallback_reason})" if response.actions.fallback_reason else ""
    print(f"ACTION LIST FOR THIS WEEK (Source: {response.actions.source.upper()}{fallback_note}):")
    for item in response.actions.items:
        print(f" [#{item.priority}] {item.title} ({item.metric_id})")
        print(f"      Recommendation: {item.recommendation}")
        print(f"      Impact:         {item.impact}")
        if item.evidence:
            print(f"      Evidence:       {item.evidence}")

    if response.warnings:
        print("-" * 70)
        print("WARNINGS:")
        for w in response.warnings:
            print(f" - {w}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run SEO audit on a website.")
    parser.add_argument("url", help="Target website URL to audit (e.g. https://www.hubspot.com)")
    parser.add_argument("--max-pages", type=int, default=settings.default_max_pages, help="Max pages to crawl (1-100)")
    args = parser.parse_args()

    try:
        response = asyncio.run(execute_audit(args.url, args.max_pages))
    except (CrawlError, ValueError) as exc:
        print(f"\nAudit failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\nUnexpected error during audit: {exc}", file=sys.stderr)
        sys.exit(1)

    print_summary(response)

    # DECISION: Audit reports are serialized to reports/<host>.json to support repeatable offline inspection.
    parsed = urlparse(response.url)
    hostname = parsed.hostname or "audit"
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"{hostname}.json"
    report_file.write_text(json.dumps(response.model_dump(), indent=2), encoding="utf-8")
    print(f"Saved complete JSON report to: {report_file}")


if __name__ == "__main__":
    main()
