"""AI Search Crawler Access metric evaluation."""

from typing import List, Optional
from protego import Protego

from app.config import settings
from app.schemas import MetricResult


def evaluate_ai_crawler_access(
    robots_parser: Optional[Protego],
    start_url: str,
    has_llms_txt: bool = False,
) -> MetricResult:
    """Evaluate access for top AI search crawlers against site robots.txt."""
    crawlers = settings.ai_crawlers
    total = len(crawlers)

    if not robots_parser:
        # Default allow if no parser available
        robots_parser = Protego.parse("")

    passed_count = 0
    details = []

    for bot in crawlers:
        # Check if bot can fetch start URL
        allowed = robots_parser.can_fetch(start_url, bot)
        if allowed:
            passed_count += 1

        note = ""
        # DECISION: Google-Extended is annotated as an AI training token rather than a distinct crawler user agent to provide accurate industry context.
        if bot == "Google-Extended":
            note = "Google-Extended is a robots.txt control token for AI training and Gemini, not a standalone web crawler."

        details.append({
            "user_agent": bot,
            "allowed": allowed,
            "note": note,
        })

    score = round(100.0 * passed_count / total, 1)
    status = "pass" if score >= settings.pass_threshold else ("warn" if score >= settings.warn_threshold else "fail")
    llms_txt_note = " (/llms.txt detected)" if has_llms_txt else " (no /llms.txt)"
    summary = f"{passed_count} of {total} AI search crawlers ({score}%) are permitted by robots.txt{llms_txt_note}."

    return MetricResult(
        id="ai_crawler_access",
        name="AI Search Crawler Access",
        mandatory=False,
        why_it_matters="AI search engines (ChatGPT, Perplexity, Claude, Google AI) require crawler permissions to index and cite your brand in answers.",
        how_measured="Tests /robots.txt against 6 key AI crawler tokens: GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and Google-Extended.",
        pass_rule="All 6 designated AI search crawlers must be permitted to crawl site pages.",
        status=status,
        score=score,
        summary=summary,
        passed=passed_count,
        total=total,
        details=details,
    )
