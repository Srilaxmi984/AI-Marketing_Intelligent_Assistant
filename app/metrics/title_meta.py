"""Title and Meta Description metric evaluation."""

from collections import Counter
from typing import List
from bs4 import BeautifulSoup

from app.config import settings
from app.crawler import FetchedPage
from app.parsing import extract_meta_description, extract_title
from app.schemas import MetricResult


def evaluate_title_meta(pages: List[FetchedPage]) -> MetricResult:
    """Evaluate title and meta description tag lengths and presence across crawled pages."""
    total = len(pages)
    if total == 0:
        return MetricResult(
            id="title_meta",
            name="Title and Meta Description",
            mandatory=True,
            why_it_matters="Page titles and descriptions form the snippet shown in search results, directly impacting click-through rates and brand visibility.",
            how_measured="Measures decoded character lengths of <head><title> (30-60 chars) and <meta name='description'> (70-160 chars) across crawled pages.",
            pass_rule="Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive.",
            status="fail",
            score=0.0,
            summary="No pages available to evaluate title and meta descriptions.",
            passed=0,
            total=0,
            details=[],
        )

    passed_count = 0
    details = []
    titles_seen = []

    for page in pages:
        soup = BeautifulSoup(page.html, "lxml")
        title, title_len = extract_title(soup)
        desc, desc_len, has_dup = extract_meta_description(soup)

        if title:
            titles_seen.append(title)

        title_ok = (title is not None) and (30 <= title_len <= 60)
        desc_ok = (desc is not None) and (70 <= desc_len <= 160)

        page_passed = title_ok and desc_ok
        if page_passed:
            passed_count += 1

        details.append({
            "url": page.final_url or page.url,
            "title": title or "",
            "title_length": title_len,
            "title_passed": title_ok,
            "meta_description": desc or "",
            "meta_description_length": desc_len,
            "meta_description_passed": desc_ok,
            "has_duplicate_meta_description": has_dup,
            "passed": page_passed,
        })

    # Identify duplicate titles across pages for informational reporting
    title_counts = Counter(titles_seen)
    duplicate_titles = [t for t, count in title_counts.items() if count > 1]
    for d in details:
        d["title_is_duplicate_on_site"] = d["title"] in duplicate_titles

    # DECISION: Title and meta scoring requires both elements to pass on a given page to reflect cohesive SERP snippet readiness.
    score = round(100.0 * passed_count / total, 1)
    status = "pass" if score >= settings.pass_threshold else ("warn" if score >= settings.warn_threshold else "fail")
    summary = f"{passed_count} of {total} pages ({score}%) meet title (30-60 chars) and meta description (70-160 chars) guidelines."

    return MetricResult(
        id="title_meta",
        name="Title and Meta Description",
        mandatory=True,
        why_it_matters="Page titles and descriptions form the snippet shown in search results, directly impacting click-through rates and brand visibility.",
        how_measured="Measures decoded character lengths of <head><title> (30-60 chars) and <meta name='description'> (70-160 chars) across crawled pages.",
        pass_rule="Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive.",
        status=status,
        score=score,
        summary=summary,
        passed=passed_count,
        total=total,
        details=details,
    )
