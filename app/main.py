"""FastAPI web application exposing the SEO audit API and static interface."""

from datetime import datetime, timezone
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.crawler import Crawler, CrawlError
from app.link_checker import LinkChecker
from app.llm import generate_action_list
from app.metrics.ai_crawler_access import evaluate_ai_crawler_access
from app.metrics.broken_links import evaluate_broken_links
from app.metrics.indexability_canonical import evaluate_indexability_canonical
from app.metrics.structured_data import evaluate_structured_data
from app.metrics.title_meta import evaluate_title_meta
from app.schemas import (
    AuditRequest,
    AuditResponse,
    CrawlStats,
    ErrorDetail,
    ErrorResponse,
)
from app.scoring import calculate_overall_score
from app.security import validate_url_security

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Marketing Intelligence Assistant",
    description="Automated SEO audit tool for marketing intelligence.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


ERROR_HTTP_MAP = {
    "INVALID_URL": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "BLOCKED_TARGET": status.HTTP_400_BAD_REQUEST,
    "ROBOTS_DISALLOWED": status.HTTP_403_FORBIDDEN,
    "UNREACHABLE_SITE": status.HTTP_502_BAD_GATEWAY,
    "NOT_HTML": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "REDIRECTED_OFFSITE": status.HTTP_422_UNPROCESSABLE_CONTENT,
    "TIMEOUT": status.HTTP_504_GATEWAY_TIMEOUT,
    "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def make_error_response(code: str, message: str) -> JSONResponse:
    # DECISION: Errors strictly follow the standard { error: { code, message } } format without leaking server stack traces.
    status_code = ERROR_HTTP_MAP.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    payload = ErrorResponse(error=ErrorDetail(code=code, message=message)).model_dump()
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return make_error_response("INVALID_URL", f"Request validation failed: {exc}")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception")
    return make_error_response("INTERNAL_ERROR", "An internal error occurred during the audit.")


@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(req: AuditRequest):
    # DECISION: Audits use a single overall deadline (settings.total_budget_s = 90s); crawl uses at most settings.crawl_budget_s (40s), link checks use remaining time, and LLM uses its own timeout.
    request_start = time.monotonic()
    deadline = request_start + settings.total_budget_s
    started_at = datetime.now(timezone.utc).isoformat()
    audit_id = str(uuid.uuid4())

    # 1. Validate URL security & SSRF
    try:
        normalized_url = validate_url_security(req.url)
    except ValueError as exc:
        msg = str(exc)
        code = "BLOCKED_TARGET" if "BLOCKED_TARGET" in msg else "INVALID_URL"
        clean_msg = msg.split(": ", 1)[-1]
        return make_error_response(code, clean_msg)

    # Validate max_pages
    max_pages = req.max_pages or settings.default_max_pages
    if max_pages < 1 or max_pages > settings.max_pages_cap:
        return make_error_response(
            "INVALID_URL",
            f"max_pages must be between 1 and {settings.max_pages_cap} inclusive.",
        )

    # 2. Run Breadth-First Crawl
    t_crawl_start = time.monotonic()
    crawl_budget = min(settings.crawl_budget_s, max(0.0, deadline - time.monotonic()))
    try:
        crawler = Crawler(max_pages=max_pages, time_budget_s=crawl_budget)
        crawl_result = await crawler.crawl(normalized_url)
    except CrawlError as exc:
        return make_error_response(exc.code, exc.message)
    except Exception as exc:
        return make_error_response("UNREACHABLE_SITE", f"Crawl failed: {exc}")
    crawl_dur = round(time.monotonic() - t_crawl_start, 2)

    # 3. Check internal links
    t_links_start = time.monotonic()
    remaining_for_links = max(0.0, deadline - time.monotonic())
    link_checker = LinkChecker()
    link_report = await link_checker.check_links(crawl_result.pages, time_budget_s=remaining_for_links)
    links_dur = round(time.monotonic() - t_links_start, 2)

    # 4. Evaluate the 5 SEO metrics in Python from crawled data
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

    # 5. Compute overall weighted score
    overall = calculate_overall_score(metrics_list)

    # 6. Generate action items via LLM or deterministic fallback
    t_llm_start = time.monotonic()
    actions = await generate_action_list(metrics_list)
    llm_dur = round(time.monotonic() - t_llm_start, 2)

    total_dur = round(time.monotonic() - request_start, 2)

    # 7. Collect warnings
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
