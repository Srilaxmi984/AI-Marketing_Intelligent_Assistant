# SEO Audit Results

## 1. Target site

**Site:** `https://www.hubspot.com`

### Why I chose it
1. **Server-rendered HTML:** pages can be inspected with `view-source`, so a static crawler (no headless browser) is enough.
2. **Crawlable:** robots.txt permits crawling of the marketing pages the audit reached (the crawler obeys robots.txt and was not blocked).
3. **AI-search signals present:** it serves `/llms.txt` and does not block the six AI crawlers I test.
4. **Realistic mix of results:** some metrics pass fully and others fail, which gives non-trivial findings:
   - Indexability and canonicals: 100% (25/25).
   - AI crawler access: 100% (6/6).
   - Structured data: 84% (21/25).
   - Title and meta description: 48% (12/25). For example, `Case Studies | HubSpot` is 22 characters, under the 30 minimum.
   - Broken links: 0 broken among the 300 links checked, but 65 links were not checked (see Caveats).

## 2. Audit report

- **Audit ID:** `adae33cf-cc78-485f-83f2-df6d957fd224`
- **Started / finished:** 2026-11-17T09:36:23Z / 2026-11-17T09:37:28Z
- **Pages crawled:** 25 (discovered: 365). Page cap: 25.
- **Duration:** 64.52 s (crawl 15.61 s, link checks 28.61 s, LLM 20.07 s)
- **Time budget truncated:** false

### Overall health score: 86.4 / 100

`title_meta (20% × 48.0) + broken_links (15% × 100.0) + indexability_canonical (25% × 100.0) + ai_crawler_access (20% × 100.0) + structured_data (20% × 84.0) = 86.4`

### Metrics

| Metric | Status | Weight | Score | Passed / Total | Pass rule |
|

---

## 2. SEO Audit Report: https://www.hubspot.com

- **Audit ID**: `6e1dd061-98f4-46da-b2b7-c8c1c2ed9afc`
- **Started At**: 2026-11-17T22:11:14.897175+00:00
- **Finished At**: 2026-11-17T22:12:51.048269+00:00
- **Pages Crawled**: 25 (discovered: 358)
- **Max Pages Cap**: 25
- **Total Duration**: 96.15 seconds
- **Stage Durations**: Crawl: 23.94s, Link Checks: 51.91s, LLM: 20.13s
- **Time Budget Scope**: Request deadline of 90s total (max 40s crawl budget, remaining time for link checks, separate 20s LLM budget across retries; worst-case total 110s)
- **Time Budget Truncated**: False

### Overall Health Score

**Score**: `86.7 / 100`

**Scoring Formula**:
> `title_meta (20.0% * 50.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 83.3) = 86.7`

### Core SEO Metrics

| Metric | Status | Weight | Score | Passed / Total | Pass Rule |
|---|---|---|---|---|---|
| **Title and Meta Description** | `FAIL` | 20.0% | 50.0% | 12 / 24 | Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive. |
| **Broken Internal Links** | `WARN` | 15.0% | 100.0% | 300 / 300 | Zero broken links. |
| **Indexability and Canonicalization** | `PASS` | 25.0% | 100.0% | 24 / 24 | A page passes only if it is indexable and declares a valid canonical URL on the same site. |
| **AI Search Crawler Access** | `PASS` | 20.0% | 100.0% | 6 / 6 | All 6 designated AI search crawlers must be permitted to crawl site pages. |
| **Structured Data (Schema.org)** | `WARN` | 20.0% | 83.3% | 20 / 24 | Each page must contain at least one JSON-LD block that parses as JSON and declares an @type (the @type is not checked against the Schema.org vocabulary). |

### Metric Summaries & Top Findings

#### Title and Meta Description (`title_meta`)
- **Summary**: 12 of 24 pages (50.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.
- **Why It Matters**: Page titles and descriptions form the snippet shown in search results, directly impacting click-through rates and brand visibility.
- **How Measured**: Measures decoded character lengths of <head><title> (30-60 chars) and <meta name='description'> (70-160 chars) across crawled pages.
- **Top Failing Items** (12 total):
  - `https://www.hubspot.com/careers`: Title length 15 (passed: False), Meta desc length 103 (passed: True)
  - `https://www.hubspot.com/company/contact`: Title length 20 (passed: False), Meta desc length 0 (passed: False)
  - `https://www.hubspot.com/company/management`: Title length 61 (passed: False), Meta desc length 33 (passed: False)
  - `https://www.hubspot.com/products/service`: Title length 54 (passed: True), Meta desc length 173 (passed: False)
  - `https://www.hubspot.com/products/content`: Title length 65 (passed: False), Meta desc length 160 (passed: True)

#### Broken Internal Links (`broken_links`)
- **Summary**: 0 broken out of 300 checked; 58 of 358 internal links were not checked because of the 300-link cap.
- **Why It Matters**: Broken links degrade user navigation and waste crawler budget, preventing search bots from indexing linked pages.
- **How Measured**: Checks internal links using HEAD with GET fallback; flags any link returning an HTTP 4xx or 5xx response code.
- **Top Failing Items**: None (all tested items passed)

#### Indexability and Canonicalization (`indexability_canonical`)
- **Summary**: 24 of 24 pages (100.0%) are indexable and declare valid canonical tags.
- **Why It Matters**: A page marked noindex cannot appear in search results, and a missing or wrong canonical lets duplicate URLs split ranking signals.
- **How Measured**: Validates absence of noindex/none directives in meta robots and X-Robots-Tag headers, and verifies that each page defines a valid, matching canonical URL in <head>.
- **Top Failing Items**: None (all tested items passed)

#### AI Search Crawler Access (`ai_crawler_access`)
- **Summary**: 6 of 6 AI search crawlers (100.0%) are permitted by robots.txt (/llms.txt detected).
- **Why It Matters**: AI search engines (ChatGPT, Perplexity, Claude, Google AI) require crawler permissions to index and cite your brand in answers.
- **How Measured**: Tests /robots.txt against 6 key AI crawler tokens: GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and Google-Extended.
- **Top Failing Items**: None (all tested items passed)

#### Structured Data (Schema.org) (`structured_data`)
- **Summary**: 20 of 24 pages (83.3%) contain valid JSON-LD markup (11 unique schema types detected across the site).
- **Why It Matters**: Structured data generates rich search results and enables AI crawlers to reliably identify entities, products, and organization data.
- **How Measured**: Inspects pages for valid JSON-LD (<script type='application/ld+json'>) blocks that parse and declare at least one @type.
- **Top Failing Items** (4 total):
  - `https://www.hubspot.com/our-story`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/careers`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/company/contact`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/company/management`: Missing Schema.org JSON-LD structured data

### Marketer Action List for This Week (Source: `FALLBACK`)

> Note on action source: LLM time limit of 20.0s exceeded across retries

**#1: Optimize Page Titles and Meta Descriptions** (`title_meta`)
- **Recommendation**: Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).
- **Business Impact**: Improves organic search snippet presentation and click-through rates on search results pages.
- **Evidence**: Score: 50.0% (12/24 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/careers`, `https://www.hubspot.com/company/contact`, `https://www.hubspot.com/company/management`, `https://www.hubspot.com/products/service`, `https://www.hubspot.com/products/content`

**#2: Deploy Schema.org JSON-LD Structured Data** (`structured_data`)
- **Recommendation**: Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.
- **Business Impact**: Enables rich search snippets and improves entity recognition across modern search engines.
- **Evidence**: Score: 83.3% (20/24 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/our-story`, `https://www.hubspot.com/careers`, `https://www.hubspot.com/company/contact`, `https://www.hubspot.com/company/management`

### Audit Warnings

- Link check cap reached: 58 of 358 internal links were not checked because of the 300-link cap.
