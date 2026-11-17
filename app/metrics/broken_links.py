"""Broken Internal Links metric evaluation."""

from app.config import settings
from app.link_checker import LinkCheckerReport
from app.schemas import MetricResult


def evaluate_broken_links(report: LinkCheckerReport) -> MetricResult:
    """Evaluate broken internal links metric from link checker results."""
    checked = report.checked_count
    broken = report.broken_count

    details = []
    for item in report.items:
        if item.status == "broken":
            details.append({
                "url": item.url,
                "status_code": item.status_code,
                "error": item.error,
                "found_on": item.found_on,
                "is_bot_blocked": item.is_bot_blocked,
            })

    links_found = report.total_found
    links_unchecked = max(0, report.total_found - checked)

    if checked == 0:
        # DECISION: When no internal links return an HTTP status, the metric is marked not applicable to prevent division by zero.
        if report.stop_reason == "time budget":
            summary = f"0 of {links_found} internal links checked; checking stopped because the time budget was reached."
        elif report.stop_reason == "link cap":
            summary = f"{links_unchecked} of {links_found} internal links were not checked because of the {settings.max_link_checks}-link cap."
        else:
            summary = "No internal links were available to check."
        return MetricResult(
            id="broken_links",
            name="Broken Internal Links",
            mandatory=True,
            why_it_matters="Broken links degrade user navigation and waste crawler budget, preventing search bots from indexing linked pages.",
            how_measured="Checks internal links using HEAD with GET fallback; flags any link returning an HTTP 4xx or 5xx response code.",
            pass_rule="Zero broken links.",
            status="warn" if links_unchecked > 0 else "pass",
            score=100.0,
            summary=summary,
            passed=0,
            total=0,
            links_found=links_found,
            links_unchecked=links_unchecked,
            stop_reason=report.stop_reason,
            details=details,
        )

    passed_count = checked - broken
    score = round(100.0 * (1.0 - (broken / checked)), 1)
    # DECISION: Broken links passes only at zero broken links AND full coverage.
    # If some discovered links were never checked (link cap or time budget), a clean
    # result is only partial evidence, so the status is "warn" rather than "pass".
    if broken > 0:
        status = "warn" if score >= settings.warn_threshold else "fail"
    elif links_unchecked > 0:
        status = "warn"
    else:
        status = "pass"

    if report.stop_reason == "time budget":
        summary = (
            f"{broken} broken out of {checked} checked; "
            f"{checked} of {links_found} internal links checked; checking stopped because the time budget was reached."
        )
    elif report.stop_reason == "link cap" or links_unchecked > 0:
        summary = (
            f"{broken} broken out of {checked} checked; "
            f"{links_unchecked} of {links_found} internal links were not checked because of the {settings.max_link_checks}-link cap."
        )
    else:
        summary = f"Found {broken} broken links out of {checked} internal links checked ({report.unreachable_count} unreachable)."

    return MetricResult(
        id="broken_links",
        name="Broken Internal Links",
        mandatory=True,
        why_it_matters="Broken links degrade user navigation and waste crawler budget, preventing search bots from indexing linked pages.",
        how_measured="Checks internal links using HEAD with GET fallback; flags any link returning an HTTP 4xx or 5xx response code.",
        pass_rule="Zero broken links.",
        status=status,
        score=score,
        summary=summary,
        passed=passed_count,
        total=checked,
        links_found=links_found,
        links_unchecked=links_unchecked,
        stop_reason=report.stop_reason,
        details=details,
    )
