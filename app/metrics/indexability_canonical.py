"""Indexability and Canonical URL metric evaluation."""

from typing import List
from bs4 import BeautifulSoup

from app.config import settings
from app.crawler import FetchedPage
from app.parsing import check_indexability, extract_canonical
from app.schemas import MetricResult


def evaluate_indexability_canonical(pages: List[FetchedPage]) -> MetricResult:
    """Evaluate indexability directives and canonical tag consistency across pages."""
    total = len(pages)
    if total == 0:
        return MetricResult(
            id="indexability_canonical",
            name="Indexability and Canonicalization",
            mandatory=False,
            why_it_matters="A page marked noindex cannot appear in search results, and a missing or wrong canonical lets duplicate URLs split ranking signals.",
            how_measured="Validates absence of noindex/none directives in meta robots and X-Robots-Tag headers, and verifies that each page defines a valid, matching canonical URL in <head>.",
            pass_rule="A page passes only if it is indexable and declares a valid canonical URL on the same site.",
            status="fail",
            score=0.0,
            summary="No pages available to evaluate indexability.",
            passed=0,
            total=0,
            details=[],
        )

    passed_count = 0
    details = []

    for page in pages:
        soup = BeautifulSoup(page.html, "lxml")
        page_url = page.final_url or page.url

        is_indexable, directives_failing = check_indexability(soup, page.headers)
        canonical_target, canonical_status, canonical_error = extract_canonical(soup, page_url)

        # Page passes only if indexable AND canonical_status in ("self", "points_elsewhere")
        # DECISION: A canonical pointing elsewhere on the same site passes indexability to accommodate valid tracking-parameter canonicalization.
        canonical_valid = canonical_status in ("self", "points_elsewhere")
        page_passed = is_indexable and canonical_valid

        if page_passed:
            passed_count += 1

        details.append({
            "url": page_url,
            "is_indexable": is_indexable,
            "indexability_failures": directives_failing,
            "canonical_status": canonical_status,
            "canonical_target": canonical_target or "",
            "canonical_error": canonical_error or "",
            "passed": page_passed,
        })

    score = round(100.0 * passed_count / total, 1)
    status = "pass" if score >= settings.pass_threshold else ("warn" if score >= settings.warn_threshold else "fail")
    summary = f"{passed_count} of {total} pages ({score}%) are indexable and declare valid canonical tags."

    return MetricResult(
        id="indexability_canonical",
        name="Indexability and Canonicalization",
        mandatory=False,
        why_it_matters="A page marked noindex cannot appear in search results, and a missing or wrong canonical lets duplicate URLs split ranking signals.",
        how_measured="Validates absence of noindex/none directives in meta robots and X-Robots-Tag headers, and verifies that each page defines a valid, matching canonical URL in <head>.",
        pass_rule="A page passes only if it is indexable and declares a valid canonical URL on the same site.",
        status=status,
        score=score,
        summary=summary,
        passed=passed_count,
        total=total,
        details=details,
    )
