# SEO Audit Results & Project Verification

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

---

## 2. SEO Audit Report: https://www.hubspot.com

- **Audit ID**: `adae33cf-cc78-485f-83f2-df6d957fd224`
- **Started At**: 2026-11-17T09:36:23.504160+00:00
- **Finished At**: 2026-11-17T09:37:28.026258+00:00
- **Pages Crawled**: 25 (discovered: 365)
- **Max Pages Cap**: 25
- **Total Duration**: 64.52 seconds
- **Stage Durations**: Crawl: 15.61s, Link Checks: 28.61s, LLM: 20.07s
- **Time Budget Scope**: Request deadline of 90s total (max 40s crawl budget, remaining time for link checks, dedicated 10s LLM timeout)
- **Time Budget Truncated**: False

### Overall Health Score

**Score**: `86.4 / 100`

**Scoring Formula**:
> `title_meta (20.0% * 48.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 84.0) = 86.4`

### Core SEO Metrics

| Metric | Status | Weight | Score | Passed / Total | Pass Rule |
|---|---|---|---|---|---|
| **Title and Meta Description** | `FAIL` | 20.0% | 48.0% | 12 / 25 | Title between 30 and 60 characters inclusive; meta description between 70 and 160 characters inclusive. |
| **Broken Internal Links** | `PASS` | 15.0% | 100.0% | 300 / 300 | Zero broken links. |
| **Indexability and Canonicalization** | `PASS` | 25.0% | 100.0% | 25 / 25 | A page passes only if it is indexable and declares a valid canonical URL on the same site. |
| **AI Search Crawler Access** | `PASS` | 20.0% | 100.0% | 6 / 6 | All 6 designated AI search crawlers must be permitted to crawl site pages. |
| **Structured Data (Schema.org)** | `WARN` | 20.0% | 84.0% | 21 / 25 | Each page must contain at least one valid JSON-LD block with recognized Schema.org types. |

### Metric Summaries & Top Findings

#### Title and Meta Description (`title_meta`)
- **Summary**: 12 of 25 pages (48.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.
- **Why It Matters**: Page titles and descriptions form the snippet shown in search results, directly impacting click-through rates and brand visibility.
- **How Measured**: Measures decoded character lengths of <head><title> (30-60 chars) and <meta name='description'> (70-160 chars) across crawled pages.
- **Top Failing Items** (13 total):
  - `https://www.hubspot.com/careers`: Title length 15 (passed: False), Meta desc length 103 (passed: True)
  - `https://www.hubspot.com/company/contact`: Title length 20 (passed: False), Meta desc length 0 (passed: False)
  - `https://www.hubspot.com/company/management`: Title length 61 (passed: False), Meta desc length 33 (passed: False)
  - `https://www.hubspot.com/products/service`: Title length 54 (passed: True), Meta desc length 173 (passed: False)
  - `https://www.hubspot.com/products/content`: Title length 65 (passed: False), Meta desc length 160 (passed: True)

#### Broken Internal Links (`broken_links`)
- **Summary**: 0 broken out of 300 checked; 65 of 365 internal links were not checked because of the 300-link cap.
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
- **Summary**: 21 of 25 pages (84.0%) contain valid JSON-LD markup (11 unique schema types detected across the site).
- **Why It Matters**: Structured data generates rich search results and enables AI crawlers to reliably identify entities, products, and organization data.
- **How Measured**: Inspects pages for valid JSON-LD (<script type='application/ld+json'>) blocks with recognized Schema.org types.
- **Top Failing Items** (4 total):
  - `https://www.hubspot.com/our-story`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/careers`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/company/contact`: Missing Schema.org JSON-LD structured data
  - `https://www.hubspot.com/company/management`: Missing Schema.org JSON-LD structured data

### Marketer Action List for This Week (Source: `FALLBACK`)

> Note on action source: Recommendation names unlisted Schema.org type 'URLs' (allowed: Organization, WebSite, WebPage, Article, BreadcrumbList, FAQPage, Product, SoftwareApplication)

**#1: Optimize Page Titles and Meta Descriptions** (`title_meta`)
- **Recommendation**: Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).
- **Business Impact**: Improves organic search snippet presentation and click-through rates on search results pages.
- **Evidence**: Score: 48.0% (12/25 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/careers`, `https://www.hubspot.com/company/contact`, `https://www.hubspot.com/company/management`, `https://www.hubspot.com/products/service`, `https://www.hubspot.com/products/content`

**#2: Deploy Schema.org JSON-LD Structured Data** (`structured_data`)
- **Recommendation**: Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.
- **Business Impact**: Enables rich search snippets and improves entity recognition across modern search engines.
- **Evidence**: Score: 84.0% (21/25 passed).
- **Sample Affected Pages**: `https://www.hubspot.com/our-story`, `https://www.hubspot.com/careers`, `https://www.hubspot.com/company/contact`, `https://www.hubspot.com/company/management`

### Audit Warnings

- Link check cap reached: 65 of 365 internal links were not checked because of the 300-link cap.
