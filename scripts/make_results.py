"""Script to run audit against TARGET_SITE and generate RESULTS.md."""

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from cli import execute_audit


async def run_and_write_results(target_url: str, max_pages: int = 25):
    print(f"Executing audit for {target_url} (max pages: {max_pages})...")
    audit = await execute_audit(target_url, max_pages=max_pages)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    md_lines = [
        f"## SEO Audit Report: {audit.url}",
        "",
        f"- **Date of Audit**: {date_str}",
        f"- **Audit ID**: `{audit.audit_id}`",
        f"- **Pages Crawled**: {audit.crawl.pages_crawled} (discovered: {audit.crawl.pages_discovered})",
        f"- **Crawl Duration**: {audit.crawl.duration_s} seconds",
        f"- **Time Budget Truncated**: {audit.crawl.truncated}",
        "",
        "### Overall SEO Health Score",
        "",
        f"**Score**: `{audit.overall.score} / 100`",
        "",
        f"**Scoring Formula**:",
        f"> `{audit.overall.formula}`",
        "",
        "### Core SEO Metrics",
        "",
        "| Metric | Status | Score | Passed / Total | Pass Rule |",
        "|---|---|---|---|---|",
    ]

    for m in audit.metrics:
        md_lines.append(
            f"| **{m.name}** | `{m.status.upper()}` | {m.score}% | {m.passed} / {m.total} | {m.pass_rule} |"
        )

    md_lines.extend([
        "",
        "### Metric Summaries & Top Findings",
        "",
    ])

    for m in audit.metrics:
        md_lines.extend([
            f"#### {m.name} (`{m.id}`)",
            f"- **Summary**: {m.summary}",
            f"- **Why It Matters**: {m.why_it_matters}",
            f"- **How Measured**: {m.how_measured}",
        ])

        failing_rows = []
        for d in m.details:
            if not d.get("passed", True) or d.get("status") == "broken" or not d.get("allowed", True):
                failing_rows.append(d)

        if failing_rows:
            md_lines.append(f"- **Top Failing Items** ({len(failing_rows)} total):")
            for item in failing_rows[:5]:
                if m.id == "title_meta":
                    md_lines.append(
                        f"  - `{item.get('url')}`: Title length {item.get('title_length')} (passed: {item.get('title_passed')}), Meta desc length {item.get('meta_description_length')} (passed: {item.get('meta_description_passed')})"
                    )
                elif m.id == "broken_links":
                    md_lines.append(
                        f"  - `{item.get('url')}`: Status {item.get('status_code')} (Found on: {', '.join(item.get('found_on', []))})"
                    )
                elif m.id == "indexability_canonical":
                    md_lines.append(
                        f"  - `{item.get('url')}`: Indexable: {item.get('is_indexable')}, Canonical status: `{item.get('canonical_status')}` (Target: `{item.get('canonical_target')}`)"
                    )
                elif m.id == "ai_crawler_access":
                    md_lines.append(
                        f"  - User-Agent `{item.get('user_agent')}`: Disallowed in robots.txt"
                    )
                elif m.id == "structured_data":
                    md_lines.append(
                        f"  - `{item.get('url')}`: Missing Schema.org JSON-LD structured data"
                    )
        else:
            md_lines.append("- **Top Failing Items**: None (all tested items passed)")

        md_lines.append("")

    md_lines.extend([
        f"### Marketer Action List for This Week (Source: `{audit.actions.source.upper()}`)",
        "",
    ])

    if audit.actions.fallback_reason:
        md_lines.append(f"> Note on action source: {audit.actions.fallback_reason}\n")

    for item in audit.actions.items:
        md_lines.extend([
            f"**#{item.priority}: {item.title}** (`{item.metric_id}`)",
            f"- **Recommendation**: {item.recommendation}",
            f"- **Business Impact**: {item.impact}",
        ])
        if item.evidence:
            md_lines.append(f"- **Evidence**: {item.evidence}")
        if item.affected_urls:
            urls_list = ", ".join(f"`{u}`" for u in item.affected_urls)
            md_lines.append(f"- **Sample Affected Pages**: {urls_list}")
        md_lines.append("")

    if audit.warnings:
        md_lines.extend([
            "### Audit Warnings",
            "",
        ])
        for w in audit.warnings:
            md_lines.append(f"- {w}")
        md_lines.append("")

    results_file = PROJECT_ROOT / "RESULTS.md"
    results_file.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Successfully generated {results_file}")


def main():
    target = settings.target_site
    max_pages = settings.default_max_pages
    asyncio.run(run_and_write_results(target, max_pages))


if __name__ == "__main__":
    main()
