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
|---|---|---|---|---|---|
| Title and Meta Description | FAIL | 20% | 48.0 | 12 / 25 | Title 30–60 chars and description 70–160 chars, inclusive |
| Broken Internal Links | PASS* | 15% | 100.0 | 300 / 300 checked | Zero broken links |
| Indexability and Canonicalization | PASS | 25% | 100.0 | 25 / 25 | Indexable and a valid same-site canonical |
| AI Search Crawler Access | PASS | 20% | 100.0 | 6 / 6 | All 6 AI crawlers permitted by robots.txt |
| Structured Data (JSON-LD) | WARN | 20% | 84.0 | 21 / 25 | At least one valid JSON-LD block with a recognised Schema.org type |

\*See Caveats: 65 of 365 links were not checked.

### Findings

**Title and meta description** (13 failing pages; first 5 shown)
- `/careers`: title 15 chars (too short); description 103 (ok)
- `/company/contact`: title 20 (short); description missing
- `/company/management`: title 61 (long); description 33 (short)
- `/products/service`: title 54 (ok); description 173 (long)
- `/products/content`: title 65 (long); description 160 (ok)

**Broken internal links:** none found among the 300 links checked.

**Indexability and canonicalization:** no issues.

**AI crawler access:** GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot and Google-Extended are all allowed; `/llms.txt` found.

**Structured data** (4 failing pages): `/our-story`, `/careers`, `/company/contact`, `/company/management` have no JSON-LD.

### Action list (source: FALLBACK)

The LLM's answer was rejected by the validator because it named an unlisted Schema.org type (`URLs`), so template actions were used.

1. **Optimise titles and meta descriptions** (`title_meta`): fix short or missing titles (30–60) and descriptions (70–160). Evidence: 12/25 pass. Start with `/careers`, `/company/contact`, `/company/management`.
2. **Add Schema.org JSON-LD** (`structured_data`): add Organization/WebSite/WebPage markup. Evidence: 21/25 pass. Start with `/our-story`, `/careers`, `/company/contact`.

## 3. Caveats

- **Link coverage:** the 300-link cap left 65 of 365 internal links unchecked. "Zero broken links" applies only to the 300 checked.
- **Sample size:** only 25 pages were crawled, starting from the home page, so company and navigation pages are over-represented.
- **Action list is a fallback:** this run did not produce LLM-written actions.
- **Warning from the audit:** link check cap reached, 65 of 365 internal links not checked.