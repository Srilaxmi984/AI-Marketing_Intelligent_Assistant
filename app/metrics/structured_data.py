"""Structured Data (JSON-LD Schema.org) metric evaluation."""

from collections import Counter
from typing import List
from bs4 import BeautifulSoup

from app.config import settings
from app.crawler import FetchedPage
from app.parsing import extract_structured_data
from app.schemas import MetricResult
from app.security import normalize_url


def evaluate_structured_data(pages: List[FetchedPage]) -> MetricResult:
    """Evaluate JSON-LD schema markup presence and valid types across crawled pages."""
    # Deduplicate pages by normalized URL
    seen_urls = set()
    deduped_pages: List[FetchedPage] = []
    for page in pages:
        p_url = normalize_url(page.final_url or page.url)
        if p_url not in seen_urls:
            seen_urls.add(p_url)
            deduped_pages.append(page)

    total = len(deduped_pages)
    if total == 0:
        return MetricResult(
            id="structured_data",
            name="Structured Data (Schema.org)",
            mandatory=False,
            why_it_matters="Structured data generates rich search results and enables AI crawlers to reliably identify entities, products, and organization data.",
            how_measured="Inspects pages for valid JSON-LD (<script type='application/ld+json'>) blocks that parse and declare at least one @type.",
            pass_rule="Each page must contain at least one JSON-LD block that parses as JSON and declares an @type (the @type is not checked against the Schema.org vocabulary).",
            status="fail",
            score=0.0,
            summary="No pages available to evaluate structured data.",
            passed=0,
            total=0,
            details=[],
        )

    passed_count = 0
    details = []
    all_types_seen = []

    for page in deduped_pages:
        soup = page.get_soup()
        has_valid, types, errors = extract_structured_data(soup)
        all_types_seen.extend(types)

        if has_valid:
            passed_count += 1

        details.append({
            "url": page.final_url or page.url,
            "has_structured_data": has_valid,
            "schema_types": types,
            "errors": errors,
            "passed": has_valid,
        })

    # Summary of detected types across the site
    type_counts = dict(Counter(all_types_seen).most_common())
    for d in details:
        d["site_wide_schema_types"] = type_counts

    score = round(100.0 * passed_count / total, 1)
    status = "pass" if score >= settings.pass_threshold else ("warn" if score >= settings.warn_threshold else "fail")
    unique_types_count = len(type_counts)
    summary = f"{passed_count} of {total} pages ({score}%) contain valid JSON-LD markup ({unique_types_count} unique schema types detected across the site)."

    return MetricResult(
        id="structured_data",
        name="Structured Data (Schema.org)",
        mandatory=False,
        why_it_matters="Structured data generates rich search results and enables AI crawlers to reliably identify entities, products, and organization data.",
        how_measured="Inspects pages for valid JSON-LD (<script type='application/ld+json'>) blocks that parse and declare at least one @type.",
        pass_rule="Each page must contain at least one JSON-LD block that parses as JSON and declares an @type (the @type is not checked against the Schema.org vocabulary).",
        status=status,
        score=score,
        summary=summary,
        passed=passed_count,
        total=total,
        details=details,
    )
