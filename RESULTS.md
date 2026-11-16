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

## 2. Real Execution Output: HubSpot Audit (CLI)

Command executed:
```bash
python cli.py https://www.hubspot.com --max-pages 25
```

```text
INFO: Starting audit for https://www.hubspot.com (max pages: 25)...
INFO: HTTP Request: GET https://www.hubspot.com/robots.txt "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/llms.txt "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/aeo-grader "HTTP/1.1 301 Moved Permanently"
INFO: HTTP Request: GET https://www.hubspot.com/ai-search-grader "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/aeo-sensor "HTTP/1.1 301 Moved Permanently"
INFO: HTTP Request: GET https://www.hubspot.com/ai-search-sensor "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/careers "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/case-studies "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/case-studies/angel-city "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/case-studies/unipart "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/case-studies/youth-on-course "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/claude "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/company/board-of-directors "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/company/contact "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/company/management "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/comparisons "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/email-signature-generator "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/free-business-tools "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/hubspot-user-groups "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/inbound-marketing "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/loop-marketing "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/make-my-persona "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/new "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/our-story "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/partners "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/partners/affiliates "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/partners/app "HTTP/1.1 301 Moved Permanently"
INFO: HTTP Request: GET https://www.hubspot.com/partners/technology "HTTP/1.1 200 OK"
INFO: HTTP Request: GET https://www.hubspot.com/partners/solutions "HTTP/1.1 200 OK"
INFO: Crawled 25 pages in 25.49s.
INFO: Checking internal links...
[262 internal links verified via asynchronous HEAD/GET checks]
INFO: Evaluating 5 SEO metrics...

======================================================================
  AI MARKETING INTELLIGENCE ASSISTANT - SEO AUDIT REPORT
======================================================================
Target URL:        https://www.hubspot.com
Audit ID:          1d73a5a1-b721-48b6-87da-997bded4e303
Pages Crawled:     25 (discovered: 262)
Crawl Duration:    25.49s
----------------------------------------------------------------------
OVERALL HEALTH SCORE: 74.4 / 100
Scoring Formula:     title_meta (20.0% * 28.0) + broken_links (15.0% * 100.0) + indexability_canonical (25.0% * 100.0) + ai_crawler_access (20.0% * 100.0) + structured_data (20.0% * 44.0) = 74.4
----------------------------------------------------------------------
THE FIVE CORE METRICS:
 1. Title and Meta Description          [FAIL]   Score:  28.0% (7/25)
    Summary: 7 of 25 pages (28.0%) meet title (30-60 chars) and meta description (70-160 chars) guidelines.
 2. Broken Internal Links               [PASS]   Score: 100.0% (262/262)
    Summary: Found 0 broken links out of 262 internal links checked (0 unreachable).
 3. Indexability and Canonicalization   [PASS]   Score: 100.0% (25/25)
    Summary: 25 of 25 pages (100.0%) are indexable and declare valid canonical tags.
 4. AI Search Crawler Access            [PASS]   Score: 100.0% (6/6)
    Summary: 6 of 6 AI search crawlers (100.0%) are permitted by robots.txt (/llms.txt detected).
 5. Structured Data (Schema.org)        [FAIL]   Score:  44.0% (11/25)
    Summary: 11 of 25 pages (44.0%) contain valid JSON-LD markup (9 unique schema types detected across the site).
----------------------------------------------------------------------
ACTION LIST FOR THIS WEEK (Source: FALLBACK):
 (Note: No GEMINI_API_KEY configured)
 [#1] Optimize Page Titles and Meta Descriptions (title_meta)
      Recommendation: Review and update pages with short or missing titles (target 30-60 characters) and meta descriptions (target 70-160 characters).
      Impact:         Improves organic search snippet presentation and click-through rates on search results pages.
      Evidence:       Score: 28.0% (7/25 passed).
 [#2] Deploy Schema.org JSON-LD Structured Data (structured_data)
      Recommendation: Add valid JSON-LD markup (e.g. Organization, Product, WebSite) across crawled pages.
      Impact:         Enables rich search snippets and improves entity recognition across modern search engines.
      Evidence:       Score: 44.0% (11/25 passed).
======================================================================

Saved complete JSON report to: reports\www.hubspot.com.json
```

---

## 3. SEO Metric Performance Breakdown

| Metric | Status | Weight | Score | Passed / Total | Pass Rule |
|---|---|---|---|---|---|
| **Title and Meta Description** | `FAIL` | 20.0% | 28.0% | 7 / 25 | Title between 30 and 60 characters; meta description between 70 and 160 characters. |
| **Broken Internal Links** | `PASS` | 15.0% | 100.0% | 262 / 262 | Zero broken links (final HTTP 4xx or 5xx). |
| **Indexability and Canonicalization** | `PASS` | 25.0% | 100.0% | 25 / 25 | Page is indexable (no noindex/none directives) and declares a valid canonical URL on the same site. |
| **AI Search Crawler Access** | `PASS` | 20.0% | 100.0% | 6 / 6 | All 6 designated AI search crawlers permitted in robots.txt. |
| **Structured Data (Schema.org)** | `FAIL` | 20.0% | 44.0% | 11 / 25 | Page contains at least one valid JSON-LD block with recognized Schema.org types. |

**Overall Score**: `74.4 / 100`

### Top Action Items for HubSpot
1. **Optimize Title and Meta Description Lengths (`title_meta`)**:
   - 18 pages failed either title (target 30–60 characters) or meta description (target 70–160 characters).
   - Examples:
     - `https://www.hubspot.com/careers`: Title length is only 15 characters ("HubSpot Careers").
     - `https://www.hubspot.com/case-studies`: Title length is only 22 characters ("HubSpot Customer Stories").
     - `https://www.hubspot.com/ai-search-grader`: Meta description is 207 characters (exceeds 160-character snippet boundary).
2. **Deploy Schema.org JSON-LD Structured Data (`structured_data`)**:
   - 14 of 25 pages currently omit JSON-LD markup entirely.
   - Adding `Organization`, `WebPage`, or `Article` schemas will enhance entity extraction for both AI engines (ChatGPT Search, Perplexity) and Google Rich Results.

---

## 4. Hand-Counted Fixture Verification: Expected vs. Measured

The fixture test suite (`tests/fixture_site/`) contains 4 pages with deliberate defects planted to prove metric determinism against hand calculations:
- `index.html`: Fully compliant (all pass)
- `page-short-title.html`: Short title (17 chars < 30)
- `page-noindex.html`: Contains `<meta name="robots" content="noindex">`
- `page-no-canonical.html`: Missing `<link rel="canonical">`
- `robots.txt`: Disallows ClaudeBot (5 of 6 allowed)
- 5 internal links tested (including 1 broken 404 target)

| Metric | Hand-Counted Expected | Measured Result | Match Status | Notes |
|---|---|---|---|---|
| **`title_meta`** | 3 / 4 (75.0%) | 3 / 4 (75.0%) | **EXACT MATCH** | 1 page has title < 30 chars |
| **`broken_links`** | 4 / 5 (80.0%) | 4 / 5 (80.0%) | **EXACT MATCH** | 1 link returns 404 |
| **`indexability_canonical`**| 2 / 4 (50.0%) | 2 / 4 (50.0%) | **EXACT MATCH** | 1 noindex page, 1 missing canonical |
| **`ai_crawler_access`** | 5 / 6 (83.3%) | 5 / 6 (83.3%) | **EXACT MATCH** | ClaudeBot disallowed in robots.txt |
| **`structured_data`** | 3 / 4 (75.0%) | 3 / 4 (75.0%) | **EXACT MATCH** | 1 page missing JSON-LD |
| **Overall Score** | **71.2 / 100** | **71.2 / 100** | **EXACT MATCH** | 0.20(75) + 0.15(80) + 0.25(50) + 0.20(83.3) + 0.20(75) = 71.2 |

---

## 5. Real Command Output: Test Suite Execution

Command executed:
```bash
python -m pytest tests/ -q
```

```text
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 2.43s
```

All 76 unit, integration, security, and fixture tests executed and passed cleanly with 0 failures and 0 warnings.

---

## 6. Action Items Generation & LLM Observation

- **Source**: `FALLBACK` (Deterministic Rule Engine)
- **Observation**:
  - The audit was executed without a `GEMINI_API_KEY` defined in `.env`.
  - The application automatically and transparently engaged its built-in deterministic fallback engine (`app/actions.py`).
  - Action items were prioritized strictly by metric score ascending (lowest scoring metric first: `title_meta` at 28.0%, then `structured_data` at 44.0%).
  - Affected URLs were pulled directly from the audit detail findings without hallucination.
  - When a valid `GEMINI_API_KEY` is provided, the LLM prompt injects these exact computed numbers and validates that returned URLs match crawled URLs, preserving strict numeric determinism.
