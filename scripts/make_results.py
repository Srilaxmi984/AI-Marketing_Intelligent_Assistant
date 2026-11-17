"""Generate RESULTS.md from saved audit JSON report, preserving top hand-written section."""

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_JSON = PROJECT_ROOT / "reports" / "www.hubspot.com.json"
RESULTS_FILE = PROJECT_ROOT / "RESULTS.md"

DEFAULT_TOP_SECTION = """# SEO Audit Results & Project Verification

## 1. Target Site Selection

**Target Site**: `https://www.hubspot.com`  
**Contact Email**: `b23ai070@kitsw.ac.in`  

### Reason for Choice
1. **Server-Side Rendered HTML**: HubSpot delivers standard server-side rendered HTML content that is readily inspectable via `view-source` without requiring client-side headless browser rendering (e.g. Chromium/Playwright).
2. **Robots Permission**: Its `robots.txt` explicitly allows crawling of general marketing paths (`User-agent: * Allow: /`), adhering to polite scraping guidelines.
3. **AI Search Readiness**: It serves an active `/llms.txt` file and does not block AI crawlers, enabling verification of modern AI search metrics.
4. **Realistic Mix of SEO Quality**: Unlike toy or sterile sites that either achieve 100% or fail completely, HubSpot exhibits a nuanced, realistic mix across its marketing properties:
   - Indexability, canonicalization, and internal links score **100.0%**.
   - AI search crawler access scores **100.0%** (all 6 designated user agents allowed, `/llms.txt` present).
   - Structured data (Schema.org JSON-LD) passes on only **44.0%** (11/25 pages).
   - Title & meta description guidelines pass on only **28.0%** (7/25 pages) due to oversized titles (>60 chars) or descriptions exceeding 160 characters.
   This provides substantial, non-trivial findings for real marketing recommendations.
"""


def extract_top_section(results_path: Path) -> str:
    """Extract hand-written target selection section up to the first horizontal rule separator."""
    if not results_path.exists():
        return DEFAULT_TOP_SECTION.strip()
    content = results_path.read_text(encoding="utf-8")
    if "---" in content:
        top_part = content.split("---", 1)[0].strip()
        return top_part
    return DEFAULT_TOP_SECTION.strip()


def build_audit_markdown(data: dict) -> str:
    """Build markdown report strictly from the saved JSON audit report."""
    crawl = data.get("crawl", {})
    overall = data.get("overall", {})
    metrics = data.get("metrics", [])
    actions = data.get("actions", {})
    warnings = data.get("warnings", [])

    lines = [
        "---",
        "",
        f"## 2. SEO Audit Report: {data.get('url', '')}",
        "",
        f"- **Audit ID**: `{data.get('audit_id', '')}`",
        f"- **Started At**: {data.get('started_at', '')}",
        f"- **Finished At**: {data.get('finished_at', '')}",
        f"- **Pages Crawled**: {crawl.get('pages_crawled', 0)} (discovered: {crawl.get('pages_discovered', 0)})",
        f"- **Max Pages Cap**: {crawl.get('max_pages', 0)}",
        f"- **Total Duration**: {data.get('total_duration_s', crawl.get('duration_s', 0.0))} seconds",
        f"- **Stage Durations**: Crawl: {data.get('stage_durations', {}).get('crawl', crawl.get('duration_s', 0.0))}s, Link Checks: {data.get('stage_durations', {}).get('link_checks', 0.0)}s, LLM: {data.get('stage_durations', {}).get('llm', 0.0)}s",
        f"- **Time Budget Scope**: Request deadline of 90s total (max 40s crawl budget, remaining time for link checks, separate 20s LLM budget across retries; worst-case total 110s)",
        f"- **Time Budget Truncated**: {crawl.get('truncated', False)}"
        + (f" ({crawl.get('truncated_reason')})" if crawl.get("truncated_reason") else ""),
        "",
        "### Overall Health Score",
        "",
        f"**Score**: `{overall.get('score', 0.0)} / 100`",
        "",
        "**Scoring Formula**:",
        f"> `{overall.get('formula', '')}`",
        "",
        "### Core SEO Metrics",
        "",
        "| Metric | Status | Weight | Score | Passed / Total | Pass Rule |",
        "|---|---|---|---|---|---|",
    ]

    weights = overall.get("weights", {})
    for m in metrics:
        weight_pct = f"{weights.get(m['id'], 0.0) * 100:.1f}%"
        lines.append(
            f"| **{m['name']}** | `{m['status'].upper()}` | {weight_pct} | {m['score']}% | {m['passed']} / {m['total']} | {m['pass_rule']} |"
        )

    lines.extend([
        "",
        "### Metric Summaries & Top Findings",
        "",
    ])

    for m in metrics:
        lines.extend([
            f"#### {m['name']} (`{m['id']}`)",
            f"- **Summary**: {m['summary']}",
            f"- **Why It Matters**: {m['why_it_matters']}",
            f"- **How Measured**: {m['how_measured']}",
        ])

        failing_rows = []
        for d in m.get("details", []):
            if not d.get("passed", True) or d.get("status") == "broken" or not d.get("allowed", True):
                failing_rows.append(d)

        if failing_rows:
            lines.append(f"- **Top Failing Items** ({len(failing_rows)} total):")
            for item in failing_rows[:5]:
                if m["id"] == "title_meta":
                    lines.append(
                        f"  - `{item.get('url')}`: Title length {item.get('title_length')} (passed: {item.get('title_passed')}), Meta desc length {item.get('meta_description_length')} (passed: {item.get('meta_description_passed')})"
                    )
                elif m["id"] == "broken_links":
                    lines.append(
                        f"  - `{item.get('url')}`: Status {item.get('status_code')} (Found on: {', '.join(item.get('found_on', []))})"
                    )
                elif m["id"] == "indexability_canonical":
                    lines.append(
                        f"  - `{item.get('url')}`: Indexable: {item.get('is_indexable')}, Canonical status: `{item.get('canonical_status')}` (Target: `{item.get('canonical_target')}`)"
                    )
                elif m["id"] == "ai_crawler_access":
                    lines.append(
                        f"  - User-Agent `{item.get('user_agent')}`: Disallowed in robots.txt"
                    )
                elif m["id"] == "structured_data":
                    lines.append(
                        f"  - `{item.get('url')}`: Missing Schema.org JSON-LD structured data"
                    )
        else:
            lines.append("- **Top Failing Items**: None (all tested items passed)")

        lines.append("")

    source = actions.get("source", "fallback").upper()
    lines.extend([
        f"### Marketer Action List for This Week (Source: `{source}`)",
        "",
    ])

    if actions.get("fallback_reason"):
        lines.append(f"> Note on action source: {actions.get('fallback_reason')}\n")

    for item in actions.get("items", []):
        lines.extend([
            f"**#{item.get('priority')}: {item.get('title')}** (`{item.get('metric_id')}`)",
            f"- **Recommendation**: {item.get('recommendation')}",
            f"- **Business Impact**: {item.get('impact')}",
        ])
        if item.get("evidence"):
            lines.append(f"- **Evidence**: {item.get('evidence')}")
        if item.get("affected_urls"):
            urls_list = ", ".join(f"`{u}`" for u in item.get("affected_urls"))
            lines.append(f"- **Sample Affected Pages**: {urls_list}")
        lines.append("")

    if warnings:
        lines.extend([
            "### Audit Warnings",
            "",
        ])
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    return "\n".join(lines).strip()


def generate_results_from_json(json_path: Path = DEFAULT_JSON, results_path: Path = RESULTS_FILE):
    """Load saved JSON report and regenerate RESULTS.md preserving hand-written top section."""
    if not json_path.exists():
        raise FileNotFoundError(f"JSON audit report not found at {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    top_section = extract_top_section(results_path)
    audit_section = build_audit_markdown(data)

    final_content = f"{top_section}\n\n{audit_section}\n"
    results_path.write_text(final_content, encoding="utf-8")
    print(f"Successfully generated {results_path} from {json_path}")


def main():
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_JSON
    generate_results_from_json(json_path)


if __name__ == "__main__":
    main()
