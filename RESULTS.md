## SEO Audit Report: https://www.hubspot.com

- **Date of Audit**: 2026-11-16 17:28:16 UTC
- **Audit ID**: `b1646427-8f86-4a45-81f3-e6129098078b`
- **Pages Crawled**: 25 (discovered: 262)
- **Crawl Duration**: 26.85 seconds
- **Time Budget Truncated**: False

### Overall SEO Health Score

**Score**: `74.4 / 100`

**Scoring Formula**:
> `title_meta (20.0% * 28.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 44.0) = 74.4`

### Core SEO Metrics

| Metric | Status | Score | Passed / Total | Pass Rule |
|---|---|---|---|---|
| **Title and Meta Description** | `FAIL` | 28.0% | 7 / 25 | Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive. |
| **Broken Internal Links** | `PASS` | 100.0% | 262 / 262 | Zero broken links. |
| **Indexability and Canonicalization** | `PASS` | 100.0% | 25 / 25 | A page passes only if it is indexable and declares a valid canonical URL on the same site. |
| **AI Search Crawler Access** | `PASS` | 100.0% | 6 / 6 | All 6 designated AI search crawlers must be permitted to crawl site pages. |
| **Structured Data (Schema.org)** | `FAIL` | 44.0% | 11 / 25 | Each page must contain at least one valid JSON-LD block with recognized Schema.org types. |

### Metric Summaries & Top Findings

#### Title and Meta Description (`title_meta`)
- **Summary**: 7 of 25 pages (28.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.
- **Why It Matters**: Page titles and descriptions form the snippet shown in search results, directly impacting click-through rates and brand visibility.
- **How Measured**: Measures decoded character lengths of <head><title> (30-60 chars) and <meta name='description'> (70-160 chars) across crawled pages.
- **Top Failing Items** (18 total):
  - `https://www.hubspot.com/ai-search-grader`: Title length 68 (passed: False), Meta desc length 207 (passed: False)
  - `https://www.hubspot.com/ai-search-sensor`: Title length 58 (passed: True), Meta desc length 166 (passed: False)
  - `https://www.hubspot.com/careers`: Title length 15 (passed: False), Meta desc length 103 (passed: True)
  - `https://www.hubspot.com/case-studies`: Title length 22 (passed: False), Meta desc length 133 (passed: True)
  - `https://www.hubspot.com/case-studies/angel-city`: Title length 10 (passed: False), Meta desc length 221 (passed: False)

#### Broken Internal Links (`broken_links`)
- **Summary**: Found 0 broken links out of 262 internal links checked (0 unreachable).
- **Why It Matters**: Broken links degrade user navigation and waste crawler budget, preventing search bots from indexing linked pages.
- **How Measured**: Checks internal links using HEAD with GET fallback; flags any link returning an HTTP 4xx or 5xx response code.
- **Top Failing Items**: None (all tested items passed)

#### Indexability and Canonicalization (`indexability_canonical`)
- **Summary**: 25 of 25 pages (100.0%) are indexable and declare valid canonical tags.
- **Why It Matters**: A page marked noindex cannot appear in search results, and a missing or wrong canonical lets duplicate URLs split ranking signals.
- **How Measured**: Validates absence of noindex/none directives in meta robots and X-Robots-Tag headers, and verifies that each page defines a valid, matching canonical URL in <head>.
- **Top Failing Items**: None (all tested items passed)

#### AI Search Crawler Access (`ai_crawler_access`)
- **Summary**: 6 of 6 AI search crawlers (100.0%) are permitted by robots.txt (/llms.txt detected).
- **Why It Matters**: AI search engines (ChatGPT, Perplexity, Claude, Google AI) require crawler permissions to index and cite your brand in answers.
- **How Measured**: Tests /robots.txt against 6 key AI crawler tokens: GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and Google-Extended.
- **Top Failing Items**: None (all tested items passed)

#### Structured Data (Schema.org) (`structured_data`)
- **Summary**: 11 of 25 pages (44.0%) contain valid JSON-LD markup (9 unique schema types detected across the site).
- **Why It Matters**: Structured data generates rich search results and enables AI crawlers to reliably identify entities, products, and organization data.
- **How Measured**: Inspects pages for valid JSON-LD (<script type='application/ld+json'>) blocks with recognized Schema.org types.
- **Top Failing Items** (14 total):
  - `https://www.hubspot.com/careers`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/case-studies`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/case-studies/angel-city`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/case-studies/unipart`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/case-studies/youth-on-course`: Missing Schema.org JSON-LD structured data

### Marketer Action List for This Week (Source: `FALLBACK`)

> Note on action source: No GEMINI_API_KEY configured

**#1: Optimize Page Titles and Meta Descriptions** (`title_meta`)
- **Recommendation**: Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).
- **Business Impact**: Improves organic search snippet presentation and click-through rates on search results pages.
- **Evidence**: Score: 28.0% (7/25 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/ai-search-grader`, `https://www.hubspot.com/ai-search-sensor`, `https://www.hubspot.com/careers`, `https://www.hubspot.com/case-studies`, `https://www.hubspot.com/case-studies/angel-city`

**#2: Deploy Schema.org JSON-LD Structured Data** (`structured_data`)
- **Recommendation**: Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.
- **Business Impact**: Enables rich search snippets and improves entity recognition across modern search engines.
- **Evidence**: Score: 44.0% (11/25 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/careers`, `https://www.hubspot.com/case-studies`, `https://www.hubspot.com/case-studies/angel-city`, `https://www.hubspot.com/case-studies/unipart`, `https://www.hubspot.com/case-studies/youth-on-course`
