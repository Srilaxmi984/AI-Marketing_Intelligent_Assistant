"""Actions generation module with issue ranking and deterministic fallback templates."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings
from app.schemas import ActionItem, ActionsResult, MetricResult


def sanitize_text(text: str, max_len: int = 100) -> str:
    """Strip control characters, newlines, and truncate text to max_len."""
    if not text:
        return ""
    # DECISION: Control characters and newlines are stripped and URLs truncated to 100 chars to sanitize untrusted page content.
    cleaned = "".join(c for c in text if c.isprintable())
    cleaned = " ".join(cleaned.split())
    if len(cleaned) > max_len:
        return cleaned[:max_len]
    return cleaned


def format_failure_reason(metric_id: str, detail: Dict[str, Any]) -> str:
    """Format exact human-readable failure reason for failing URL or asset."""
    if metric_id == "title_meta":
        reasons = []
        t_len = detail.get("title_length", 0)
        if not detail.get("title_passed", True):
            if t_len == 0:
                reasons.append("missing title")
            elif t_len > settings.title_max_chars:
                reasons.append(f"title {t_len} chars, over {settings.title_max_chars}")
            else:
                reasons.append(f"title {t_len} chars, under {settings.title_min_chars}")

        m_len = detail.get("meta_description_length", 0)
        if not detail.get("meta_description_passed", True):
            if m_len == 0:
                reasons.append("missing meta description")
            elif m_len > settings.meta_max_chars:
                reasons.append(f"meta {m_len} chars, over {settings.meta_max_chars}")
            else:
                reasons.append(f"meta {m_len} chars, under {settings.meta_min_chars}")
        return "; ".join(reasons) or "title/meta out of range"

    if metric_id == "structured_data":
        if not detail.get("has_jsonld"):
            return "no JSON-LD found"
        return "invalid JSON-LD markup"

    if metric_id == "broken_links":
        return detail.get("error") or f"HTTP {detail.get('status_code')}"

    if metric_id == "indexability_canonical":
        failures = detail.get("failures", [])
        if failures:
            return "; ".join(failures)
        return "canonical or indexability issue"

    if metric_id == "ai_crawler_access":
        ua = detail.get("user_agent", "")
        return f"{ua} blocked in robots.txt"

    return "failed pass rule"


def collect_ranked_issues(metrics: List[MetricResult]) -> List[Dict[str, Any]]:
    """Rank audit issues by business impact: weight * (100 - score)."""
    issues = []

    for m in metrics:
        weight = settings.metric_weights.get(m.id, 0.0)
        deficit = 100.0 - m.score
        impact = weight * deficit

        failing_urls = []
        failing_items = []
        for d in m.details:
            if not d.get("passed", True) or d.get("status") == "broken" or not d.get("allowed", True):
                raw_url = d.get("url") or d.get("user_agent") or ""
                clean_url = sanitize_text(raw_url, max_len=100)
                if clean_url and clean_url not in failing_urls:
                    failing_urls.append(clean_url)
                    reason = format_failure_reason(m.id, d)
                    failing_items.append({"url": clean_url, "failure_reason": reason})

        evidence = f"Score: {m.score}% ({m.passed}/{m.total} passed)."
        issues.append({
            "metric_id": m.id,
            "metric_name": m.name,
            "score": m.score,
            "impact_score": round(impact, 2),
            "evidence": evidence,
            "failing_urls": failing_urls[:10],
            "failing_items": failing_items[:10],
        })

    # Sort descending by impact score
    issues.sort(key=lambda x: x["impact_score"], reverse=True)
    return issues


FALLBACK_TEMPLATES = {
    "title_meta": {
        "title": "Optimize Page Titles and Meta Descriptions",
        "recommendation": "Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).",
        "impact": "Improves organic search snippet presentation and click-through rates on search results pages.",
    },
    "broken_links": {
        "title": "Fix Broken Internal Links",
        "recommendation": "Update or remove all internal links returning HTTP 4xx or 5xx error responses.",
        "impact": "Restores search crawler navigation paths and eliminates broken user journeys.",
    },
    "indexability_canonical": {
        "title": "Resolve Indexability and Canonical Directives",
        "recommendation": "Ensure indexable pages do not contain noindex directives and declare valid, self-referencing canonical URLs.",
        "impact": "Prevents accidental de-indexing and consolidates ranking signals to authoritative URLs.",
    },
    "ai_crawler_access": {
        "title": "Enable AI Search Engine Crawlers in robots.txt",
        "recommendation": "Update robots.txt directives to permit GPTBot, ClaudeBot, and PerplexityBot on public marketing assets.",
        "impact": "Ensures company content and products can be cited in generative AI answers.",
    },
    "structured_data": {
        "title": "Deploy Schema.org JSON-LD Structured Data",
        "recommendation": "Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.",
        "impact": "Enables rich search snippets and improves entity recognition across modern search engines.",
    },
}


def generate_fallback_actions(
    ranked_issues: List[Dict[str, Any]],
    reason: str = "Fallback template used",
    model: Optional[str] = None,
) -> ActionsResult:
    """Generate deterministic, marketer-friendly action items from ranked issues."""
    items: List[ActionItem] = []
    priority = 1

    # Take top issues with deficits
    for issue in ranked_issues:
        if priority > 5:
            break
        # Include issues that have a deficit, or top issues if all pass
        if issue["impact_score"] > 0 or priority == 1:
            template = FALLBACK_TEMPLATES.get(issue["metric_id"])
            if not template:
                continue

            # DECISION: Action item evidence is strictly constructed in code from crawler numbers, never by the LLM.
            item = ActionItem(
                priority=priority,
                metric_id=issue["metric_id"],
                title=template["title"],
                recommendation=template["recommendation"],
                impact=template["impact"],
                affected_urls=issue["failing_urls"][:5],
                evidence=issue["evidence"],
            )
            items.append(item)
            priority += 1

    return ActionsResult(
        source="fallback",
        model=model,
        fallback_reason=reason,
        items=items,
    )
